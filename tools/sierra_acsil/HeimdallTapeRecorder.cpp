// HEIMDALL — read-only Time & Sales + best bid/ask recorder for Sierra Chart (ACSIL).
//
// Records EVERY s_TimeAndSales record for the chart's symbol into append-only CSV files:
//   <OutputFolder>\<SYMBOL>_<YYYYMMDD UTC>.csv       one line per T&S record
//   <OutputFolder>\<SYMBOL>_events_<YYYYMMDD>.csv   start / backfill / gap / marker / reset events
//
// Fields are exactly those Sierra exposes in s_TimeAndSales (scstructures.h). Nothing is inferred:
//   seq            s_TimeAndSales::Sequence (Sierra-assigned, >=1, may wrap; NOT an exchange sequence number)
//   type           0 = SC_TS_MARKER (gap), 1 = SC_TS_BID (trade at bid or lower),
//                  2 = SC_TS_ASK (trade at ask or higher), 6 = SC_TS_BIDASKVALUES (quote update)
//   sc_utc_us      s_TimeAndSales::DateTime (UTC) as Unix microseconds (Sierra resolution; data-feed time)
//   local_proc_ns  host wall clock (GetSystemTimePreciseAsFileTime) when THIS study call processed the batch.
//                  It is NOT a network receive time: it lags receipt by up to the chart update interval.
//   batch          study-call counter; backfill = 1 for records already in the T&S array at first call.
// UNAVAILABLE in s_TimeAndSales (never inferred here): exchange sequence number, MBO/order IDs, queue position.
//
// No order, position, or trade-management function is called. The Heimdall money path is untouched.

#include "sierrachart.h"
#include <windows.h>
#include <cstdio>
#include <cstdint>

SCDLLName("Heimdall Tape Recorder")


static int64_t LocalUnixNs()
{
	FILETIME ft;
	GetSystemTimePreciseAsFileTime(&ft);
	ULARGE_INTEGER u;
	u.LowPart = ft.dwLowDateTime;
	u.HighPart = ft.dwHighDateTime;
	return (static_cast<int64_t>(u.QuadPart) - 116444736000000000LL) * 100;  // 100 ns ticks since 1601 -> ns since 1970
}

static void UtcYmd(int64_t unix_us, char* out, size_t n)
{
	time_t secs = static_cast<time_t>(unix_us / 1000000);
	struct tm t;
	gmtime_s(&t, &secs);
	snprintf(out, n, "%04d%02d%02d", t.tm_year + 1900, t.tm_mon + 1, t.tm_mday);
}

static void AppendLine(const SCString& path, const char* line)
{
	FILE* f = nullptr;
	if (fopen_s(&f, path.GetChars(), "ab") == 0 && f != nullptr)  // append-only; prior bytes never rewritten
	{
		fputs(line, f);
		fflush(f);
		fclose(f);
	}
}

static SCString SafeSymbol(const SCString& s)
{
	SCString out;
	for (int i = 0; i < s.GetLength(); ++i)
	{
		char c = s[i];
		bool ok = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.';
		char buf[2] = { ok ? c : '_', 0 };
		out += buf;
	}
	return out;
}

static void LogEvent(const SCString& folder, const SCString& sym, int64_t local_ns, const char* kind, int64_t a, int64_t b)
{
	char ymd[16];
	UtcYmd(local_ns / 1000, ymd, sizeof(ymd));
	SCString path;
	path.Format("%s\\%s_events_%s.csv", folder.GetChars(), sym.GetChars(), ymd);
	char line[256];
	snprintf(line, sizeof(line), "%lld,%s,%lld,%lld\n", static_cast<long long>(local_ns), kind, static_cast<long long>(a), static_cast<long long>(b));
	AppendLine(path, line);
}

SCSFExport scsf_HeimdallTapeRecorder(SCStudyInterfaceRef sc)
{
	SCInputRef InFolder = sc.Input[0];

	if (sc.SetDefaults)
	{
		sc.GraphName = "Heimdall Tape Recorder (read-only)";
		sc.StudyDescription = "Appends every Time & Sales record (trades + bid/ask updates) for the chart symbol to CSV. No trading functions.";
		sc.AutoLoop = 0;
		sc.UpdateAlways = 1;          // called every chart update interval even when no new bar forms
		sc.GraphRegion = 0;
		sc.FreeDLL = 0;
		InFolder.Name = "Output Folder";
		InFolder.SetPathAndFileName("C:\\SierraChart\\Data\\HeimdallTape");
		return;
	}

	int64_t& r_LastSeq = sc.GetPersistentInt64(1);   // last Sequence written (0 = none yet)
	int64_t& r_Batch = sc.GetPersistentInt64(2);
	int64_t& r_Gaps = sc.GetPersistentInt64(3);

	SCString folder = InFolder.GetPathAndFileName();
	CreateDirectoryA(folder.GetChars(), nullptr);
	SCString sym = SafeSymbol(sc.Symbol);

	c_SCTimeAndSalesArray ts;
	sc.GetTimeAndSales(ts);
	const int n = ts.Size();
	if (n == 0)
		return;

	const int64_t local_ns = LocalUnixNs();
	const bool first_call = (r_Batch == 0);
	++r_Batch;
	if (first_call)
		LogEvent(folder, sym, local_ns, "start_backfill_records", n, static_cast<int64_t>(ts[n - 1].Sequence));

	const float vol_mult = sc.MultiplierFromVolumeValueFormat();
	char ymd[16];
	char line[512];
	SCString path;
	char path_ymd[16] = { 0 };
	FILE* out = nullptr;              // one append-only handle per call; reopened only when the UTC date changes

	for (int i = 0; i < n; ++i)
	{
		s_TimeAndSales rec = ts[i];
		const int64_t seq = static_cast<int64_t>(rec.Sequence);

		if (!first_call)
		{
			if (seq <= r_LastSeq)
			{
				if (r_LastSeq - seq > 1000000)   // large backward jump: Sierra sequence wrapped or was reset
				{
					LogEvent(folder, sym, local_ns, "sequence_reset_or_wrap", r_LastSeq, seq);
					r_LastSeq = seq - 1;
				}
				else
					continue;                    // already written
			}
			if (seq > r_LastSeq + 1)
			{
				++r_Gaps;
				LogEvent(folder, sym, local_ns, "sequence_gap", r_LastSeq, seq);
			}
		}
		if (rec.Type == SC_TS_MARKER)
			LogEvent(folder, sym, local_ns, "sc_ts_marker", seq, rec.DateTime.ToUNIXTimeInMicroseconds());

		rec *= sc.RealTimePriceMultiplier;
		const int64_t sc_utc_us = rec.DateTime.ToUNIXTimeInMicroseconds();
		UtcYmd(sc_utc_us, ymd, sizeof(ymd));
		if (strcmp(ymd, path_ymd) != 0)
		{
			strcpy_s(path_ymd, ymd);
			path.Format("%s\\%s_%s.csv", folder.GetChars(), sym.GetChars(), ymd);
			if (out != nullptr) { fflush(out); fclose(out); out = nullptr; }
			if (fopen_s(&out, path.GetChars(), "ab") != 0)   // append-only; prior bytes never rewritten
				out = nullptr;
		}
		snprintf(line, sizeof(line), "%lld,%d,%lld,%lld,%.10g,%.10g,%.10g,%.10g,%.10g,%.10g,%.10g,%.10g,%d,%d,%u,%lld,%d\n",
			static_cast<long long>(seq), static_cast<int>(rec.Type), static_cast<long long>(sc_utc_us), static_cast<long long>(local_ns),
			rec.GetPrice(), rec.GetVolume() * vol_mult, rec.GetBid(), rec.GetAsk(),
			rec.GetBidSize() * vol_mult, rec.GetAskSize() * vol_mult,
			static_cast<double>(rec.TotalBidDepth), static_cast<double>(rec.TotalAskDepth),
			static_cast<int>(rec.UnbundledTradeIndicator), static_cast<int>(rec.TradeIndicator),
			static_cast<unsigned>(rec.NumberOfTrades), static_cast<long long>(r_Batch), first_call ? 1 : 0);
		if (out == nullptr)
		{
			LogEvent(folder, sym, local_ns, "write_failed", seq, 0);
			return;                          // do not advance r_LastSeq: the record is retried next call
		}
		fputs(line, out);
		r_LastSeq = seq;
	}
	if (out != nullptr) { fflush(out); fclose(out); }
}
