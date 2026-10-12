**English** | [Español](README.es.md)

# Recommended profile — X6810-GL / BSG 9.7 V32

[x6810-gcam-bsg-9.7-v32-recommended.xml](x6810-gcam-bsg-9.7-v32-recommended.xml) is the supplied `recomend_settings.xml`, renamed to identify the device, port, version and purpose. The content is preserved byte for byte.

| Property | Value |
|---|---|
| Tested port | [MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk) |
| Package | `com.android.MGC_9_7_047` |
| Tested device/system | Infinix X6810-GL / Android 16 GSI |
| Result | Tested and works perfectly; telephoto OIS tested and working |
| Format | SharedPreferences XML, root `map` |
| Preferences | 755 unique keys: 727 strings, 11 booleans, 10 integers, 7 longs |
| Size | 47,229 bytes |
| XML SHA-256 | `1b4014581d5bc07b0b3678ba4cea6be7e3bef7cd7f532e51d02e8907aa0ee9f9` |
| Signed APK SHA-256 | `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89` |

## Import

1. Install BSG V32 as a normal app and grant the required permissions. The system module is optional; [RAW/OIS/HD48](https://github.com/SRE-0/infinix_x6810_raw) is separate.
2. Download the XML to an accessible folder, such as Downloads, preserving `.xml`.
3. Export your current settings using `Save config`, then select the supplied XML with `Load config`. Labels can vary with the app language. [BSG configuration guide](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/help/0/) documents loading from any folder.
4. Reopen the app if requested and select the available sensors. The saved camera IDs are `0,1,2`.
5. Restore your exported configuration to undo the settings change.

Do not copy this snapshot directly into `/data/data` or apply it with the historical V18 overlay tool. Releases deliver the XML separately; installing the system module does not import it at boot.

## Significant settings

| Preference | Saved value | Meaning |
|---|---|---|
| `camera.ois_forced_photo_mode` | boolean `true` | Requests photo OIS; telephoto OIS tested and working |
| `pref_video_stabilization_ois_key` | string `1` | Separate video OIS preference |
| `camera.lenstoggles_enable` | boolean `true` | Lens selection controls |
| `lens_wl_key` | `0,1,2` | Camera IDs on the tested device |
| `pref_camera_raw_output_option_available_key` | `1` | Makes the RAW option available |
| `pref_camera_raw_output_key` | `0` | DNG saving disabled; enable in the app if needed |
| `pref_video_resolution` | `RES_1080P` | Saved video resolution |

The snapshot also preserves AWB, exposure, denoising, sharpening and lib-patcher values. `_0`, `_1` and `_2` suffixes identify per-camera settings; these do not automatically transfer to other devices or ports. Internal state includes counters, startup flags, a version value and a local thumbnail URI. No photo, APK or complete app-data backup is contained in the XML.

The tested result applies to V32 on Android 16 GSI; this documentation change did not perform new mobile tests. Other compatible GCam APKs may be installed, but this profile does not certify every port or Android 11. HD48 must be requested as a JPEG stream by the app; the XML does not produce 48 MP RAW or force every GCam to use HD48.

## Historical V18 references

`x6810-gcam-bsg-v18-recommended.xml` and `gcam-bsg-v18.json` remain historical experiments. They are not the current recommended profile. `tools/configure_mgc_photo.py` operates on those small V18 overlays, not this full V32 snapshot.
