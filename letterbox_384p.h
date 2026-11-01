#pragma once
#include <stdint.h>

// Bench-only, full-width fit on a 4:3, 384-line display. Profile describes
// DISPLAY aspect, not pixel dimensions, and does not configure input width.
// 0: 4:3; 1: 16:9; 2: square-pixel 800x480 (5:3, rounded to 307 lines).
struct Letterbox384Geometry {
    uint16_t lines, top, bottom, rate;
};
constexpr uint16_t letterbox384Lines(uint8_t profile)
{
    return profile == 1 ? 288 : profile == 2 ? 307 : 384;
}
constexpr uint16_t downscale480Rate(uint16_t lines)
{
    // Candidate accumulator model calibrated at 480 -> 384 (rate 1024).
    // Other ratios require full-frame hardware validation.
    return uint16_t((4096UL * (480 - lines) + lines / 2) / lines);
}
constexpr Letterbox384Geometry letterbox384(uint8_t profile)
{
    return {letterbox384Lines(profile),
            uint16_t((384 - letterbox384Lines(profile)) / 2),
            uint16_t(384 - letterbox384Lines(profile) - (384 - letterbox384Lines(profile)) / 2),
            downscale480Rate(letterbox384Lines(profile))};
}
