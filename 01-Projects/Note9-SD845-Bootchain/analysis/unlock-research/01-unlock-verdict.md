# SM-N960U Bootloader Unlock — Research Verdict

**Project:** `01-Projects/Note9-SD845-Bootchain` · **Document type:** evidence review / verdict
**Research window (web captures):** 2026-11-12 → 2026-11-13 (America/New_York)
**Author:** Atlas agent (researcher role) · **Status:** hypothesis-free; all claims below carry a citation and a capture timestamp

> This note answers the project's load-bearing question: *can the reviewed unit's
> bootloader actually be unlocked?* It does **not** resolve the wider RE question
> (what exactly the r7→r9 delta patched) — that stays with the bindiff pipeline.
> Per the operating contract: evidence and disconfirming examples first; paid-service
> claims are recorded as **vendor claims**, not verified facts (no purchase, no token,
> no device-side test was performed — purchase would require owner approval).

---

## 0. TL;DR

| Question | Answer |
|---|---|
| Is this SM-N960U bootloader unlockable today? | **No reliable route exists.** |
| Community consensus | No US-marketed Samsung Snapdragon device is bootloader-unlockable; exceptions were always patched via bootloader update (V0latyle, Oct 2024). |
| Paid-token claim examined (UNSAMLOCK) | Service existed (2021–2023), claims real unlocks, **but** per its own device table Note 9 is supported **only on BL V1–V7**. |
| This unit's bootloader | **BL V9** (`N960USQU9FVG2` — final-ever N960U build, Android 10 / One UI 2.5, SPL Jun/Jul 2022) → **out of the paid service's documented range**, and inside the window those services said was re-patched ("post-February 2021"). |
| Can we downgrade to V7? | No — Samsung anti-rollback (fused bootloader counter); the "unlock window" firmware is unreachable and was the pool that got locked. |
| Is the SIM/carrier unlock the same thing? | No — SIM unlock (already done on this unit) is carrier discretion and explicitly out of scope of bootloader-unlock services. |

**Bottom line for the device:** AT&T-market SM-N960U, on its final firmware, bootloader
rev 9, OEM-unlock toggle absent (as on every US/Canada unit) — **locked for good** under
current knowledge. The unlock story effectively ended Oct 2023 (reg / service threads
closed) and Oct 2024 (last community re-checks).

---

## 1. Device context (owner-provided + build evidence)

- **Model:** SM-N960U (US Snapdragon SDM845) — carrier market **AT&T** (per owner, Nov 2026).
- **Current software:** Android 10, **One UI 2.5**, security patch **July 2022** (per owner) →
  build **`N960USQU9FVG2`**, the *last firmware ever released* for SM-N960U:
  - Built/released **Jul 21, 2022** (samfrew entry) · **SPL 2022-06-01** documented on the
    Samsung USA firmware page (carrier listing published **Aug 30, 2022**) —
    [s11-fvg2.md](../../.research/s11-fvg2.md) (captured 2026-11-13).
  - Device-displayed SPL "July 2022" vs documented "2022-06-01": same build, minor doc/display
    skew; no newer N960U build exists regardless.
- **Bootloader revision:** `USQU**9**` in the build string → **BL rev 9**
  (revision = 5th character from the right, per UNSAMLOCK FAQ
  [unsamlock.md#L309](../../.research/unsamlock.md#L309)).
- Prior state (owner history): was on **rev 7**-era firmware (`N960U1UES7FUA1`, Jan 2021 —
  [s10-fua1.md](../../.research/s10-fua1.md)), i.e. the *last build inside* the "unlock window",
  since updated to the final V9 build. Per UNSAMLOCK's own warnings
  ([unsamlock.md#L174-L176](../../.research/unsamlock.md#L174-L176)) that V9 step is exactly the
  "March 2021 security update and later will bypass the unlock token" case.
- **SIM/carrier:** carrier-unlocked (BYOD). AT&T SIM-unlock is a separate, already-resolved
  matter (paid-off postpaid device); it grants **network** access, not bootloader access.

---

## 2. Why it is locked: the community consensus (evidence)

### 2.1 V0latyle (Retired XDA Moderator) — Oct 26, 2024
Thread *"still no bootloader unlock method for SM-N960U?"* — answering the exact unit question
(post #11→12):
[xda-still-no-unlock.md#L361-L365](../../.research/xda-still-no-unlock.md#L361-L365)
(captured 2026-11-12; thread [xdaforums.com/t/4545333](https://xdaforums.com/t/still-no-bootloader-unlock-for-sm-n960u.4545333/)):

> "Except for some very specific examples, I am not aware of any Samsung Snapdragon devices
> marketed in the US that are bootloader unlockable. There have been some here and there -
> such as the Galaxy S6 or S7 - but this was almost always patched with a bootloader update.
> There is no specific identifier; you just have to keep your ear to the ground, so to speak..."

To the same poster (attit, "OEM unlock is missing, how can I root"):
[xda-still-no-unlock.md#L419](../../.research/xda-still-no-unlock.md#L419) — points to the
Magisk install requirements (unlocked bootloader required) and the XDA Rule 5 prohibition on
paid unlock services.

### 2.2 joshw0000 (XDA Senior Member) — "SM-N960U Bootloader Unlock/ROM's?"
Asked about an **AT&T** SM-N960U in that thread:
[s13-att-note9.md#L12-L14](../../.research/s13-att-note9.md#L12-L14)
(captured 2026-11-13; thread [xdaforums.com/t/4116349](https://xdaforums.com/t/sm-n960u-bootloader-unlock-roms.4116349/)):

> "No bootloader unlock on United States Snapdragon, no OEM unlock. Setting date back only
> works on International devices. You can flash unlocked firmware (U1) but that doesn't unlock
> your bootloader it's just unbranded firmware."

### 2.3 Android Enthusiasts Stack Exchange — Q242005 (Kali/Diag attempt)
The *only* answer on the "unlock N960U via Kali/Qualcomm diag" question:
[se-kali-unlock.md#L206](../../.research/se-kali-unlock.md#L206)
(captured 2026-11-12; question [android.stackexchange.com/q/242005](https://android.stackexchange.com/questions/242005/)):

> "US variants can't be unlocked in regular ways. If you insist, see UnSamLock (paid)."

→ Community's single pointer to the paid route (examined in §3), which is itself now closed
and out of range for this unit's BL rev.

---

## 3. The alternative claim examined: paid SR-token services

### 3.1 UNSAMLOCK (XDA thread 4215101) — the strongest paid claim
Open Jan 8, 2021 ([unsamlock.md#L169](../../.research/unsamlock.md#L169)) · **closed by
moderators Oct 19, 2023** ([L229](../../.research/unsamlock.md#L229)); operator account
(afaneh92) subsequently disabled. Full-page capture:
[unsamlock.md](../../.research/unsamlock.md) (1707 lines, captured 2026-11-12).

**Claimed mechanism** (OP text):
- Device-specific DID via download mode or `adb shell getprop ro.boot.em.did`
  ([L192-L196](../../.research/unsamlock.md#L192-L196));
- Paid token delivered in 1–36 h; **single chance — flashing a combination token first
  invalidates it** ([L204-L210](../../.research/unsamlock.md#L204-L210));
- Requires modified ODIN to flash ([L210](../../.research/unsamlock.md#L210));
- "USA/Canada devices has no oem unlock toggle" ([L212](../../.research/unsamlock.md#L212));
- Knox trips; bootloader stays unlocked **within the same bootloader revision**
  ([L214-L218](../../.research/unsamlock.md#L214-L218));
- S1/SN5 "CROM"-style service; token unlocks the bootloader to an Exynos-style state
  (WV1–WV4 bootloaders); **WV5+ "captive" bootloader partitions (modem/BL locking) are not
  unlockable** — this is the mechanism limit the OP documented ([L174-L176, L220](../../.research/unsamlock.md#L174-L176), plus FAQ threads).

**Supported-device table — the binding constraint** ([L255-L307](../../.research/unsamlock.md#L255-L307)).
Relevant rows (verbatim):

```
Galaxy Note 8 N950U, N950U1, N950W, BL V1-8                       (L256)
Galaxy S8   G950U, G950U1 and G950W, BL V1-8                      (L258)
Galaxy Note 9 N960U, N960U1 and N960W, BL V1-7                    (L262)
Galaxy S9+  G965U, G965U1 and G965W, BL V1-9                      (L263)
Galaxy S9   G960U, G960U1 and G960W, BL V1-9                      (L264)
Galaxy Note10+ N975U.., BL V1-5                                   (L268)
```

→ **Note 9 US/Canada is capped at BL V1–V7.** This unit is on **V9**. The service's own
supported range excludes it. (Same listing in the mirror FAQ post:
[s9-feb2021.md#L24-L25](../../.research/s9-feb2021.md#L24-L25).)

**Firmware-window warnings** ([unsamlock.md#L174-L176, L220](../../.research/unsamlock.md#L174-L176)):

> "If you are already updated post February 2021, do not update to April 2023 security update
> (XXXXXXXXXXWCX) or later... Samsung has patched the bootloader unlock again on those updates."
> "****NOTE: The OneUI 3.1 bootloader (March 2021 security update and later) will bypass the
> unlock token, Do not update or bump your bootloader version.****"
> "Updating to 2021 march security update will bypass the unlock on most devices, don't update
> to higher bootloader version."

→ This unit's FVG2 (Jul 2022) is **past the February-2021 cutoff** *and* at the highest rev.
Even the "don't take the patch update" strategy is moot: the patch update already ran.

**SIM-unlock disclaimer** ([L224](../../.research/unsamlock.md#L224)):

> "unlocking your bootloader does not mean that you will be able to unlock the SIM lock.
> Unlocking your SIM lock is at the discretion of your operator/carrier and is not part of the
> bootloader unlocking scope."

### 3.2 SamPWND (elliwigy.com / thecustomdroid) — second paid service checked
Captured status page: [sampwnd.md](../../.research/sampwnd.md) + follow-up
[s6-sampwnd-status.md](../../.research/s6-sampwnd-status.md) (2026-11-12).
Supports US/Canada Samsung token unlocks via IMEI check, but the supported-model surface starts
at **S10/Note10 era and newer** — **the Note 9 family is not in its device list**. Not a path
for this unit either.

### 3.3 Assessment of the paid claim
- Plausible in period: the two services are independent and their device tables cross-check
  (unSAM.lock covers S8–A32 including Note 9 V1–7; SamPWND starts later).
- **But** for *this* unit both are dead ends: BL V9 > V7, post-Feb-2021 firmware, service
  closed Oct 2023 (operator disabled), and XDA banned paid-unlock discussion (Rule 5).
- No purchase or token test was performed (approval gate) — recorded as vendor claims only.

---

## 4. Disconfirming examples and dead ends checked

| Route seen online | Verdict | Evidence |
|---|---|---|
| **Date-rollback / time-trick to re-show OEM toggle** | International/Exynos only; does not work on US Snapdragon | joshw0000, [s13-att-note9.md#L14](../../.research/s13-att-note9.md#L14); V0latyle BL-region-follows-CSC discussion |
| **Flash U1 "carrier-unlocked" firmware** | Not an unlock — just unbranded (same locked BL) | joshw0000, same line; [s3-u1v7.md](../../.research/s3-u1v7.md) |
| **"Unlock bootloader on any Qualcomm device" guides (androidgreek)** | e/OS user claimed a forced unlock on N960U in **Jan 2021** — era-specific; method was Samsung's region-unlock path, dead on post-Feb-2021 builds and on carrier U CSCs | [efound-n960u.md](../../.research/efound-n960u.md) (captured 2026-11-12; [e.foundation thread 25792](https://community.e.foundation/t/samsung-note-9-n960u-snapdragon-unlock-bootloader-instructions/25792)); cross-linked S20U G988U1 example |
| **Root-first (Magisk patched AP) without unlock** | Requires unlocked bootloader — circular | V0latyle pointing attit to [Magisk requirements](https://topjohnwu.github.io/Magisk/install.html#requirements), [xda-still-no-unlock.md#L419](../../.research/xda-still-no-unlock.md#L419) |
| **Kali / Qualcomm diag-channel unlock** | No method given; SE community answer: "can't be unlocked in regular ways"; paid pointer only | [se-kali-unlock.md#L206](../../.research/se-kali-unlock.md#L206) |
| **Custom-ROM community (lineage/e/OS) for the SD845 Note 9** | Exists **only for the international Snapdragon N9600** (`crownqltechn`: unofficial LOS 17.1 by klabit87, /e/OS-T 2.7 builds, TWRP 3.5.2) — **not** the US N960U; Exynos N960F (`crownlte`) official LOS is no longer maintained | [s12-n9600-rom.md](../../.research/s12-n9600-rom.md), [s4-sd-roms.md](../../.research/s4-sd-roms.md), [s7-n9600-twrp.md](../../.research/s7-n9600-twrp.md) |
| **e/OS / custom firmware for N960U itself** | Community answers: no unlock → no custom OS for US SD units | [efound-n960u.md](../../.research/efound-n960u.md), [s8-efound-url.md](../../.research/s8-efound-url.md) (e-f thread 25792) |

**Reddit cross-confirmation (Nov 2024), AT&T unit exactly like ours:**
r/GalaxyNote9 *"Out of Luck with Bootloader Unlocks on SM-N960U?"*
([reddit.com/r/GalaxyNote9/comments/1ix8n4d](https://www.reddit.com/r/GalaxyNote9/comments/1ix8n4d/),
captured in [s13-att-note9.md#L1-L5](../../.research/s13-att-note9.md#L1-L5)) — user with an
AT&T-inherited SM-N960U; thread confirms no unlock path.

---

## 5. Verdict, with what-remains-known

1. **Locked, permanently under current knowledge.** Installed BL rev 9 exceeds every documented
   unlock path for this model (paid service cap V7); firmware is the final, post-window build;
   anti-rollback prevents reaching V7-window firmware; no public exploit exists (last checks:
   XDA Oct 2024, Reddit Nov 2024, SE 2025).
2. **Carrier side adds nothing.** AT&T sells an already-SIM-unlockable device; bootloader
   unlock is not part of any US carrier unlock scope (V0latlee consensus + UNSAMLOCK disclaimer
   L224).
3. **The one remaining "if":** a future public V9-era exploit. Nothing known of one; the only
   historically working vector (SR token) died with the service closures in 2023.
4. **For the R&D project:** this unit is a **locked reference device**. The r7→r9 bindiff
   (commits 346782c / d115f35, `analysis/modules/`) remains the correct *forensic* program —
   precisely documenting *what* the final build changed is the academically valuable output,
   no unlocked hardware required. Any on-device dynamic testing of an unlock would require a
   second unit from the unlockable family (N960F Exynos global, or international Snapdragon
   N9600 with its own crownqltechn community) — that would be a purchase decision for the owner.

---

## 6. Evidence index (captures, 2026-11-12 → 2026-11-13)

| # | Source | Captured at | Key claims |
|---|--------|-------------|------------|
| s1 | [.research/s1-unlock.md](../../.research/s1-unlock.md) | 11-12 | First-pass unlock landscape |
| s2 | [.research/s2-roms.md](../../.research/s2-roms.md) | 11-12 | ROM/root landscape N960U |
| s3 | [.research/s3-u1v7.md](../../.research/s3-u1v7.md) | 11-12 | U1 V7 firmware identity |
| s4 | [.research/s4-sd-roms.md](../../.research/s4-sd-roms.md) | 11-12 | LOS crownlte N960F / N9600 SD variants |
| s5 | [.research/s5-services.md](../../.research/s5-services.md) | 11-12 | Paid unlock service landscape |
| s6 | [.research/s6-sampwnd-status.md](../../.research/s6-sampwnd-status.md) | 11-12 | SamPWND status check |
| s7 | [.research/s7-n9600-twrp.md](../../.research/s7-n9600-twrp.md) | 11-12 | TWRP crownqltechn |
| s8 | [.research/s8-efound-url.md](../../.research/s8-efound-url.md) | 11-12 | e/OS thread URL + context |
| s9 | [.research/s9-feb2021.md](../../.research/s9-feb2021.md) | 11-12 | "Feb 2021" cutoff & device table mirror |
| s10 | [.research/s10-fua1.md](../../.research/s10-fua1.md) | 11-13 | FUA1 = last U1 (Jan 2021) |
| s11 | [.research/s11-fvg2.md](../../.research/s11-fvg2.md) | 11-13 | FVG2 = final U9 (Jul 2022, SPL 06/2022) |
| s12 | [.research/s12-n9600-rom.md](../../.research/s12-n9600-rom.md) | 11-13 | LOS 17.1 crownqltechn (N9600) |
| s13 | [.research/s13-att-note9.md](../../.research/s13-att-note9.md) | 11-13 | AT&T-N960U questions & answers (Reddit 2024, XDA) |
| — | [.research/unsamlock.md](../../.research/unsamlock.md) | 11-12 | Full XDA 4215101 capture (1707 lines) |
| — | [.research/xda-still-no-unlock.md](../../.research/xda-still-no-unlock.md) | 11-12 | Full XDA 4545333 capture (701 lines) |
| — | [.research/efound-n960u.md](../../.research/efound-n960u.md) | 11-12 | e/OS thread: Jan-2021 forced-unlock (era-restricted) |
| — | [.research/se-kali-unlock.md](../../.research/se-kali-unlock.md) | 11-12 | SE Q242005 (Kali/diag — no route) |
| — | [.research/sampwnd.md](../../.research/sampwnd.md) | 11-12 | SamPWND support list (no Note 9) |
| — | [.research/devto-sd-root.md](../../.research/devto-sd-root.md) | 11-12 | dev.to SD-root writeup (method context) |
| — | [.research/xda-n960u-unlock.md](../../.research/xda-n960u-unlock.md), [xda-missing-toggle-fix.md](../../.research/xda-missing-toggle-fix.md) | 11-12 | Older threads: N960U unlock / missing-toggle fixes |

Caveats: forum/web captures are point-in-time snapshots; paid-service text is vendor-authored
and unverified by test; "no public exploit exists" is a strong negative claim supported only by
community silence — it cannot be logically proven.

## 7. Open decisions for the owner

- [ ] Accept unit as permanently stock (One UI 2.5 final) and continue forensic-only RE. *(Recommended)*
- [ ] Authorize purchase of an unlockable-family second unit (N960F or N9600) for on-device research.
- [ ] If a new exploit claim appears, re-open this note and re-verify against §3 limits before any purchase.
