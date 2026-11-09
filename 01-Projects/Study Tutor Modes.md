# Study Tutor Modes — Atlas

**Status:** Governance integration; not a deployed tutor app, database, scheduled agent, or connected learner profile.

Study projects share `[[02-Agents/Skills/study-tutor-governance]]` and the vendored Jane Street `socratic-tutor` protocol. This is a **policy and agent-skill integration**, not a claim that a ChatGPT conversation, automation, or an external application automatically loads these files.

| Surface | Tutor behavior | Current boundary |
| --- | --- | --- |
| Japanese (N4→N3 bridge) | Japanese-first decomposition, learner teach-back, natural practice and spaced recall | Preserve already authorized Mon/Wed/Fri sessions. No private progress in Git. |
| Japanese Music/BL immersion | Use real learner-supplied media as optional conversational prompts and transfer exercises | Experimental adapter lives on `feat/japanese-immersion-music-bridge`; no claim of live history sync or auth. |
| Thai and other language study | Diagnose actual structure/particle/register understanding and test transfer | Do not assume an established language profile or persist private sessions. |
| Programming / Python coursework | Prediction, debugging, explanatory code exercises, textbook-sensitive checks | Direct factual and homework requests remain direct unless tutoring is asked for. |
| Future study branches | Inherit the same consent gate and evidence-based 0–5 mastery tracking | Add a subject adapter only when needed, without bypassing Atlas privacy/approval gates. |

**Using in agents:** Read `AGENTS.md` then `02-Agents/Skills/study-tutor-governance.md`; load `.agents/skills/socratic-tutor/SKILL.md` when tutoring is explicitly authorized. Agents without automatic skill discovery can follow those paths manually.

**Handoff:** The learner may request "save state" and privately transfer the compact subskill/evidence record into another session. Avoid storing personally identifying or detailed progress records in this public vault. All persistence is opt-in.
