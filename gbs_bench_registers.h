// Raw LCD bench transactions. Never included in the normal build.
#pragma once
struct BenchRegisterOp { uint8_t segment, address, mask, value; };
constexpr unsigned BenchMaxOps = 128;
BenchRegisterOp benchOps[BenchMaxOps];
uint8_t benchBefore[BenchMaxOps], benchAfter[BenchMaxOps];
uint8_t benchSnapshot[6 * 240];
volatile uint8_t benchJob = 0; // 1: snapshot, 2: masked write batch
uint16_t benchOpCount = 0;
uint8_t benchActions = 0;
uint32_t benchJobId = 0;
bool benchJobOk = false;
String benchJobError;

String benchHex(const uint8_t *bytes, size_t count) {
    const char digits[] = "0123456789abcdef";
    String s; s.reserve(count * 2);
    for (size_t i = 0; i < count; ++i) { s += digits[bytes[i] >> 4]; s += digits[bytes[i] & 15]; }
    return s;
}
int benchUnhex(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
void applyBenchRegisterJob() {
    const uint8_t job = benchJob;
    if (!job) return;
    benchJobError = "";
    benchJobOk = false;
    if (job == 2 && (uopt->presetPreference != Output384P || rto->presetID != 7)) {
        benchJobError = "384p must remain active";
        benchJob = 0; return;
    }
    if (job == 1) {
        for (unsigned seg = 0; seg < 6; ++seg) {
            for (unsigned address = 0; address < 240; address += 16) {
                GBS::read(seg, address, benchSnapshot + seg * 240 + address, 16);
                yield();
            }
        }
        benchJobOk = true;
    } else {
        const uint8_t dac = GBS::DAC_RGBS_PWDNZ::read();
        // Read every original before muting or writing, so undo is exact.
        for (unsigned i = 0; i < benchOpCount; ++i)
            benchBefore[i] = GBS::read(benchOps[i].segment, benchOps[i].address);
        GBS::DAC_RGBS_PWDNZ::write(0);
        for (unsigned i = 0; i < benchOpCount; ++i) {
            const auto &o = benchOps[i];
            const uint8_t current = GBS::read(o.segment, o.address);
            GBS::write(o.segment, o.address, uint8_t((current & ~o.mask) | (o.value & o.mask)));
        }
        if (benchActions & 1) latchPLLAD();
        if (benchActions & 2) ResetSDRAM();
        GBS::DAC_RGBS_PWDNZ::write(dac);
        benchJobOk = true;
        for (unsigned i = 0; i < benchOpCount; ++i) {
            const auto &o = benchOps[i];
            benchAfter[i] = GBS::read(o.segment, o.address);
            if ((benchAfter[i] & o.mask) != (o.value & o.mask)) benchJobOk = false;
        }
        if (!benchJobOk) benchJobError = "masked readback mismatch";
    }
    benchJob = 0; // publish only after result buffers are complete
}
void registerBenchRegisterEndpoints() {
    server.on("/bench/registers", HTTP_POST, [](AsyncWebServerRequest *request) {
        if (benchPending || benchJob) { request->send(409, "text/plain", "bench busy"); return; }
        if (!request->hasParam("action", true)) { request->send(400); return; }
        const String action = request->getParam("action", true)->value();
        if (action == "snapshot") {
            benchOpCount = 0; benchJobOk = false; ++benchJobId; benchJob = 1;
        } else if (action == "apply") {
            if (uopt->presetPreference != Output384P || rto->presetID != 7) { request->send(409, "text/plain", "select 384p first"); return; }
            if (!request->hasParam("ops", true)) { request->send(400); return; }
            const String encoded = request->getParam("ops", true)->value();
            if (!encoded.length() || encoded.length() % 8 || encoded.length() > BenchMaxOps * 8) { request->send(400); return; }
            // Validate the entire transaction before publishing any work.
            for (unsigned n = 0; n < encoded.length(); ++n)
                if (benchUnhex(encoded[n]) < 0) { request->send(400); return; }
            const unsigned count = encoded.length() / 8;
            for (unsigned i = 0; i < count; ++i) {
                uint8_t b[4];
                for (unsigned k = 0; k < 4; ++k)
                    b[k] = (benchUnhex(encoded[i*8+k*2]) << 4) | benchUnhex(encoded[i*8+k*2+1]);
                if (b[0] > 5 || b[1] >= 240 || !b[2]) { request->send(400); return; }
                for (unsigned j = 0; j < i; ++j)
                    if (benchOps[j].segment == b[0] && benchOps[j].address == b[1]) { request->send(400, "text/plain", "duplicate register"); return; }
                benchOps[i] = {b[0], b[1], b[2], b[3]};
            }
            uint8_t actions = 0;
            if (request->hasParam("actions", true)) {
                const String flags = request->getParam("actions", true)->value();
                if (flags.length() != 1 || flags[0] < '0' || flags[0] > '3') { request->send(400); return; }
                actions = flags[0] - '0';
            }
            benchActions = actions; benchOpCount = count; benchJobOk = false; ++benchJobId; benchJob = 2;
        } else { request->send(400); return; }
        request->send(202, "application/json", "{\"id\":" + String(benchJobId) + "}");
    });
    server.on("/bench/registers", HTTP_GET, [](AsyncWebServerRequest *request) {
        if (benchJob) { request->send(200, "application/json", "{\"id\":" + String(benchJobId) + ",\"busy\":true}"); return; }
        String result = "{\"id\":" + String(benchJobId) + ",\"busy\":false,\"ok\":";
        result += benchJobOk ? "true" : "false";
        result += ",\"error\":\"" + benchJobError + "\"";
        if (benchOpCount) {
            result += ",\"before\":\"" + benchHex(benchBefore, benchOpCount) + "\",\"after\":\"" + benchHex(benchAfter, benchOpCount) + "\"";
        } else result += ",\"registers\":\"" + benchHex(benchSnapshot, sizeof(benchSnapshot)) + "\"";
        result += "}";
        request->send(200, "application/json", result);
    });
}
