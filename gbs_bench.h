// LCD bench instrumentation only; included after firmware types and helpers.
#pragma once
#include "letterbox_384p.h"

// Volatile, bounded adjustments for LCD bench work. Never persisted to presets.
struct BenchField { const char *name; uint16_t minimum; uint16_t maximum; };
const BenchField benchFields[] = {
    {"ht", 1400, 2850}, {"vt", 390, 550}, {"vscale", 128, 1023},
    {"vbypass", 0, 1}, {"dec", 0, 3}, {"ybypass", 0, 1}, {"uvbypass", 0, 1},
    {"ifvs", 0, 1}, {"ifflip", 0, 1}, {"offset", 200, 320},
    {"route", 0, 2}, {"hsstart", 0, 1024}, {"hsstop", 0, 1024},
    {"vsstart", 0, 12}, {"vsstop", 0, 12},
    {"vblankstart", 380, 549}, {"vblankstop", 0, 160},
    {"yphase", 0, 1}, {"hscale", 320, 900},
    {"rate", 0, 4095}, {"viir", 0, 1},
    {"osd", 0, 1}, {"osdy", 0, 45}, {"ifvbstart", 0, 524}, {"ifvbstop", 0, 524},
    {"ifhbstart", 0, 1500}, {"ifhbstop", 0, 1500},
    {"hblankstart", 900, 2800}, {"hblankstop", 100, 700},
    {"phbstart", 900, 2800}, {"phbstop", 0, 2800},
    {"pvbstart", 0, 549}, {"pvbstop", 0, 160}, {"freerun", 1, 1},
    {"dram", 0, 1}, {"ifhb1start", 0, 255}, {"ifhb1stop", 0, 255},
    {"extvbstart", 380, 549}, {"extvbstop", 0, 160}, {"resetmemory", 1, 1}, {"aspect", 0, 2},
    {"ifhrst", 512, 2047}, {"iflinestart", 0, 4095}, {"iflinestop", 512, 4095},
    {"ifhbinstart", 0, 2047}, {"ifhbinstop", 0, 2047},
    {"fetch", 128, 384}, {"freeze", 0, 1},
    {"exthbstart", 900, 2800}, {"exthbstop", 0, 700}, {"rasterclock", 0, 2},
};
volatile uint8_t benchPending = 0;
volatile uint16_t benchValue = 0;
void applyBenchAdjustment()
{
    if (!benchPending) return;
    uint8_t field = benchPending - 1;
    uint16_t value = benchValue;
    benchPending = 0;
    if (uopt->presetPreference != Output384P || rto->presetID != 7) {
        SerialM.println("BENCH refused: 384p must be active");
        return;
    }
    switch (field) {
        case 0: GBS::VDS_HSYNC_RST::write(value); break;
        case 1:
            GBS::VDS_VSYNC_RST::write(value);
            GBS::VDS_VSYN_SIZE1::write(value + 2);
            GBS::VDS_VSYN_SIZE2::write(value + 2); break;
        case 2: GBS::VDS_VSCALE::write(value); break;
        case 3: GBS::VDS_VSCALE_BYPS::write(value); break;
        case 4: GBS::MADPT_VSCALE_DEC_FACTOR::write(value); break;
        case 5: GBS::MADPT_Y_VSCALE_BYPS::write(value); break;
        case 6: GBS::MADPT_UV_VSCALE_BYPS::write(value); break;
        case 7: GBS::IF_VS_SEL::write(value); break;
        case 8: GBS::IF_VS_FLIP::write(value); break;
        case 9: GBS::PB_CAP_OFFSET::write(value); break;
        case 10: GBS::OUT_SYNC_SEL::write(value); break;
        case 11: GBS::VDS_HS_ST::write(value); break;
        case 12: GBS::VDS_HS_SP::write(value); break;
        case 13: GBS::VDS_VS_ST::write(value); break;
        case 14: GBS::VDS_VS_SP::write(value); break;
        case 15: GBS::VDS_DIS_VB_ST::write(value); break;
        case 16: GBS::VDS_DIS_VB_SP::write(value); break;
        case 17: GBS::MADPT_SEL_PHASE_INI::write(value); break;
        case 18: GBS::VDS_HSCALE::write(value); break;
        case 19: setVerticalDownscaleRate(value); break;
        case 20: GBS::MADPT_VIIR_BYPS::write(value); break;
        case 21: if (value) osdManager.menuOn(); else osdManager.menuOff(); break;
        case 22:
            GBS::OSD_COMMAND_FINISH::write(0);
            GBS::OSD_MENU_VER_START::write(value);
            GBS::OSD_COMMAND_FINISH::write(1); break;
        case 23: GBS::IF_VB_ST::write(value); break;
        case 24: GBS::IF_VB_SP::write(value); break;
        case 25: GBS::IF_HB_ST2::write(value); break;
        case 26: GBS::IF_HB_SP2::write(value); break;
        case 27: GBS::VDS_DIS_HB_ST::write(value); break;
        case 28: GBS::VDS_DIS_HB_SP::write(value); break;
        case 29: GBS::VDS_HB_ST::write(value); break;
        case 30: GBS::VDS_HB_SP::write(value); break;
        case 31: GBS::VDS_VB_ST::write(value); break;
        case 32: GBS::VDS_VB_SP::write(value); break;
        case 33:
            GBS::VDS_SYNC_EN::write(0); GBS::VDS_FLOCK_EN::write(0);
            GBS::VDS_DIF_FR_SEL_EN::write(0); GBS::VDS_DFIELD_EN::write(0); break;
        case 34: GBS::VDS_D_RAM_BYPS::write(value); break;
        case 35: GBS::IF_HB_ST::write(value); break;
        case 36: GBS::IF_HB_SP::write(value); break;
        case 37: GBS::VDS_EXT_VB_ST::write(value); break;
        case 38: GBS::VDS_EXT_VB_SP::write(value); break;
        case 39: ResetSDRAM(); break;
        case 40: {
            // Atomic profile application: preserve raster totals/clock/sync,
            // fit all 480 source lines into the centered content window.
            const auto geometry = letterbox384(value);
            GBS::DAC_RGBS_PWDNZ::write(0);
            GBS::MADPT_VSCALE_DEC_FACTOR::write(0);
            GBS::MADPT_Y_VSCALE_BYPS::write(0);
            GBS::MADPT_UV_VSCALE_BYPS::write(0);
            setVerticalDownscaleRate(geometry.rate);
            GBS::MADPT_SEL_PHASE_INI::write(1);
            GBS::MADPT_SEL_PHASE_INI::write(0);
            GBS::VDS_VSCALE_BYPS::write(1);
            GBS::VDS_VSCALE::write(1023);
            GBS::VDS_DIS_VB_SP::write(24 + geometry.top);
            GBS::VDS_DIS_VB_ST::write(408 - geometry.bottom);
            GBS::VDS_EXT_VB_SP::write(24 + geometry.top);
            GBS::VDS_EXT_VB_ST::write(408 - geometry.bottom);
            GBS::VDS_VB_SP::write(20 + geometry.top);
            GBS::VDS_VB_ST::write(18 + geometry.top);
            GBS::DAC_RGBS_PWDNZ::write(1);
            break;
        }
        case 41: GBS::IF_HSYNC_RST::write(value); break;
        case 42: GBS::IF_LINE_ST::write(value); break;
        case 43: GBS::IF_LINE_SP::write(value); break;
        case 44: GBS::IF_HBIN_ST::write(value); break;
        case 45: GBS::IF_HBIN_SP::write(value); break;
        case 46: GBS::PB_FETCH_NUM::write(value); break;
        case 47: if (value) freezeVideo(); else unfreezeVideo(); break;
        case 48: GBS::VDS_EXT_HB_ST::write(value); break;
        case 49: GBS::VDS_EXT_HB_SP::write(value); break;
        case 50: {
            // Keep the line/field rates approximately unchanged while testing
            // lower pixel clocks. All horizontal boundaries move together.
            const uint16_t oldTotal = GBS::VDS_HSYNC_RST::read();
            const uint16_t newTotal = value == 0 ? 2640 : value == 1 ? 2200 : 1650;
            const uint8_t clock = value == 0 ? 0x55 : value == 1 ? 0x45 : 0x25;
            const auto scaled = [oldTotal, newTotal](uint16_t v) -> uint16_t {
                return (uint32_t(v) * newTotal + oldTotal / 2) / oldTotal;
            };
            uint16_t scale = (uint32_t(GBS::VDS_HSCALE::read()) * oldTotal + newTotal / 2) / newTotal;
            if (scale > 1023) { SerialM.println("BENCH refused: hscale overflow"); break; }
            GBS::DAC_RGBS_PWDNZ::write(0);
            GBS::VDS_HS_ST::write(scaled(GBS::VDS_HS_ST::read()));
            GBS::VDS_HS_SP::write(scaled(GBS::VDS_HS_SP::read()));
            GBS::VDS_DIS_HB_ST::write(scaled(GBS::VDS_DIS_HB_ST::read()));
            GBS::VDS_DIS_HB_SP::write(scaled(GBS::VDS_DIS_HB_SP::read()));
            GBS::VDS_EXT_HB_ST::write(scaled(GBS::VDS_EXT_HB_ST::read()));
            GBS::VDS_EXT_HB_SP::write(scaled(GBS::VDS_EXT_HB_SP::read()));
            GBS::VDS_HB_ST::write(scaled(GBS::VDS_HB_ST::read()));
            GBS::VDS_HB_SP::write(scaled(GBS::VDS_HB_SP::read()));
            GBS::VDS_HSCALE::write(scale);
            GBS::VDS_HSYNC_RST::write(newTotal);
            GBS::PLL648_CONTROL_01::write(clock);
            GBS::DAC_RGBS_PWDNZ::write(1);
            break;
        }
    }
    char message[96];
    snprintf(message, sizeof(message), "BENCH set %s=%u\n", benchFields[field].name, value);
    SerialM.print(message);
}
