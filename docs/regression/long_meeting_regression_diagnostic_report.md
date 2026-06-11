# Long-Meeting Regression Diagnostic Report

Date recorded: 2026-06-11

## Purpose

This report diagnoses the lowest-scoring transcript-baseline cases before making another summarization or extraction change.

The previous broad long-meeting cue expansion was intentionally rejected because it did not improve M03, L02, L03, or L04. This report is evidence-gathering only.

## Scope

- Diagnostic/reporting only
- No product-code changes
- No fixture changes
- No evaluator changes
- Generated temporary actual-output JSON files are not committed

## Baseline Snapshot

- Evaluated cases: 4
- Passed cases: 0
- Failed cases: 4
- Average score: 0.0677

## Target Cases

| Case | Category | Score | Decisions | Actions | Risks | Context |
|---|---:|---:|---:|---:|---:|---:|
| M03 | medium | 0.05 | 0/6 (0.0) | 0/1 (0.0) | 0/5 (0.0) | 1/3 (0.3333) |
| L02 | long | 0.05 | 0/7 (0.0) | 0/5 (0.0) | 0/5 (0.0) | 1/3 (0.3333) |
| L03 | long | 0.1 | 0/7 (0.0) | 0/5 (0.0) | 0/6 (0.0) | 2/3 (0.6667) |
| L04 | long | 0.0708 | 1/9 (0.1111) | 0/5 (0.0) | 0/7 (0.0) | 1/4 (0.25) |

## Diagnostic Details

## M03 — AMI TS3005b LCD remote-control design discussion

- Category: medium
- Score: 0.05
- Expected fixture: `backend/tests/fixtures/meeting_regression/M03_AMI_TS3005b_25min_degraded.expected.json`
- Actual output: `backend/tests/tmp/meeting_regression_actual/M03_AMI_TS3005b_25min_degraded.actual.json`

### Decisions

- Recall: 0/6 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.1 | Include a dedicated control for switching between one-digit and two-digit channel entry. | [00:48.48-00:48.99] User Interface Designer (C): One question. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 2 | False | 0.0769 | Target the new product primarily at customers younger than forty while not intentionally excluding older customers. | And um we will also take a look at new project requirements, um if you haven't heard about them yet. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 3 | False | 0.0 | Use an LCD or touchscreen screen as the current design direction. |  | No useful candidate was generated for this expected item. |
| 4 | False | 0.0909 | Keep rubber or physical buttons as a backup plan if the LCD screen is too expensive. | And um we will also take a look at new project requirements, um if you haven't heard about them yet. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 5 | False | 0.0 | Put teletext and less important settings in separate LCD menus or submenus. |  | No useful candidate was generated for this expected item. |
| 6 | False | 0.0625 | Use automatic standby or shutdown behavior after a short idle period rather than requiring users to manually turn the remote on first. | And then of course we have to take a decision on the remote control functions and we have some more time, forty minutes. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |

### Actions

- Recall: 0/1 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.325 | Owner: Marketing Expert; Action: Post or share LCD cost information in the project mail folder if cost information is received. | • # M03 — AMI TS3005b, first 25 minutes, degraded audio • Official speaker-role mapping: • - A: Industrial Designer • - B: Project Manager • - C: User Interface Designer • - D: Marketing Expert • [00:13.79-00:15.55] Industrial Designer (A): Good morning, again. • [00:48.48-00:48.99] User Interface Designer (C): One question. | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |

### Risks

- Recall: 0/5 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.0 | LCD or touchscreen screens may be too expensive for the low-cost production target. |  | No useful candidate was generated for this expected item. |
| 2 | False | 0.0 | An LCD-only design may not appeal to older users. |  | No useful candidate was generated for this expected item. |
| 3 | False | 0.0 | LCD screens may drain batteries quickly. |  | No useful candidate was generated for this expected item. |
| 4 | False | 0.0 | Requiring users to turn the remote on before use could hurt usability. |  | No useful candidate was generated for this expected item. |
| 5 | False | 0.0 | Different TV models may handle two-digit channel entry differently. |  | No useful candidate was generated for this expected item. |

### Context

- Recall: 1/3 (0.3333)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | True | 0.5714 | The team continues the remote-control product design discussion. | # M03 — AMI TS3005b, first 25 minutes, degraded audio [00:13.79-00:15.55] Industrial Designer (A): Good morning, again. [00:48.48-00:48.99] User Interface Designer (C): One question. [00:54.83-00:55.56] User Interface Designer (C): Send Um here we are already at our uh functional design meeting. The opening, which we are doing now, um and the special note, I'm project manager but on the meetings I'm also the secretary, which means I will make uh minutes as I did of the previous meeting. [02:47.57-02:49.98] Industrial Designer (A): And one qu... | Matched. |
| 2 | False | 0.3333 | The discussion focuses on button behavior, target market, LCD/touchscreen use, cost, power supply, and basic remote-control functions. | # M03 — AMI TS3005b, first 25 minutes, degraded audio [00:13.79-00:15.55] Industrial Designer (A): Good morning, again. [00:48.48-00:48.99] User Interface Designer (C): One question. [00:54.83-00:55.56] User Interface Designer (C): Send Um here we are already at our uh functional design meeting. The opening, which we are doing now, um and the special note, I'm project manager but on the meetings I'm also the secretary, which means I will make uh minutes as I did of the previous meeting. [02:47.57-02:49.98] Industrial Designer (A): And one qu... | Related evidence exists, but the output does not match the expected item closely enough. |
| 3 | False | 0.3077 | The audio is degraded, so wording may be imperfect, but the main design decisions and concerns should still be captured. | # M03 — AMI TS3005b, first 25 minutes, degraded audio [00:13.79-00:15.55] Industrial Designer (A): Good morning, again. [00:48.48-00:48.99] User Interface Designer (C): One question. [00:54.83-00:55.56] User Interface Designer (C): Send Um here we are already at our uh functional design meeting. The opening, which we are doing now, um and the special note, I'm project manager but on the meetings I'm also the secretary, which means I will make uh minutes as I did of the previous meeting. [02:47.57-02:49.98] Industrial Designer (A): And one qu... | Related evidence exists, but the output does not match the expected item closely enough. |

## L02 — AMI EN2001b annotation-format and information-density planning meeting

- Category: long
- Score: 0.05
- Expected fixture: `backend/tests/fixtures/meeting_regression/L02_AMI_EN2001b_50min.expected.json`
- Actual output: `backend/tests/tmp/meeting_regression_actual/L02_AMI_EN2001b_50min.actual.json`

### Decisions

- Recall: 0/7 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.2222 | Use the existing segment structure as the main target for attaching information-density values. | [16:48.74-17:04.30] Speaker B (B): So this whole information we would then store in this Ah, no, that I don't have access to because I didn't download like there's this one meta information file where it describes the structure of all the files and describes which um which attributes they bring in. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 2 | False | 0.1429 | Create or consider an additional annotation file that links to existing segment IDs and adds a numeric density or information value. | [16:48.74-17:04.30] Speaker B (B): So this whole information we would then store in this Ah, no, that I don't have access to because I didn't download like there's this one meta information file where it describes the structure of all the files and describes which um which attributes they bring in. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.1333 | Treat segment-level output as the desired final representation, even if some methods first produce word-level values. | [02:16.18-02:46.58] Speaker B (B): So what I've been thinking is maybe if we try to really make sense together of the X_M_L_ format to be sure that we can all produce the data that we are producing in a way or at least I mean I guess my data I'll probably load in from completely different way anyway because it's matrix, but all this stuff that goes with annotation, that we have it in the right format. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 4 | False | 0.0 | Use a preliminary entropy-style score as a possible prototype measure. |  | No useful candidate was generated for this expected item. |
| 5 | False | 0.0833 | Keep Rainbow/information-gain exploration separate while also considering an entropy-based alternative. | [16:48.74-17:04.30] Speaker B (B): So this whole information we would then store in this Ah, no, that I don't have access to because I didn't download like there's this one meta information file where it describes the structure of all the files and describes which um which attributes they bring in. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 6 | False | 0.125 | Explore combining utterance-based or segment-based scores with word-based scores outside the XML file, possibly in the software, so weights can be adjusted dynamically. | [16:48.74-17:04.30] Speaker B (B): So this whole information we would then store in this Ah, no, that I don't have access to because I didn't download like there's this one meta information file where it describes the structure of all the files and describes which um which attributes they bring in. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 7 | False | 0.0526 | Map values back to existing segments using start/end times, word references, or segment IDs rather than inventing a new unrelated structure. | [12:10.39-12:17.95] Speaker A (A): But I think these segments are perhaps not exactly what we are looking at, because that's just o one tying all the others together. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |

### Actions

- Recall: 0/5 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.25 | Owner: Speaker C; Action: Create files from delimited segments or otherwise prepare data in a form that can be merged with the annotation structure. | Speaker C [25:49.06-25:53.70] Speaker C (C): does is that you you put in some documents | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 2 | False | 0.325 | Owner: Speaker B; Action: Provide a vocabulary or dictionary with an entropy score for each word as a byproduct of the LSA work. | Speaker B [32:03.48-32:07.74] Speaker B (B): You you do wouldn't you need several documents for each category? | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 3 | False | 0.25 | Owner: Speaker C; Action: Continue working on Rainbow and try to find a way to tie Rainbow output into the shared segment or word structure. | Speaker C [25:49.06-25:53.70] Speaker C (C): does is that you you put in some documents | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 4 | False | 0.35 | Owner: Speaker B; Action: Spend time understanding the NITE data system so the team can avoid manually parsing and recombining time values where possible. | Speaker B [02:16.18-02:46.58] Speaker B (B): So what I've been thinking is maybe if we try to really make sense together of the X_M_L_ format to be sure that we can all produce the data that we are producing in a way or at least I mean I guess my data I'll probably load in from completely different way anyway because it's matrix, but all this stuff that goes with annotation, that we have it in the right format. | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 5 | False | 0.3182 | Owner: Speaker C; Action: Investigate whether it is feasible to produce a single value per segment from the word-level output. | Speaker C [25:53.70-26:00.07] Speaker C (C): , and you have several documents per category. | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |

### Risks

- Recall: 0/5 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.0 | The team does not yet fully understand the internal NITE XML data structure or loading framework. |  | No useful candidate was generated for this expected item. |
| 2 | False | 0.1111 | Manual parsing and remapping of times, words, and segments may be fragile or inefficient. | [46:42.35-46:54.11] Speaker B (B): sort of this is going from word to word or it this is going from time to time and then there has to be a way then for you say okay, this concerns these following words, and then just make make a simple mean over them. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.1429 | Rainbow output may not preserve the word order or values needed for direct mapping back to the source words. | [46:42.35-46:54.11] Speaker B (B): sort of this is going from word to word or it this is going from time to time and then there has to be a way then for you say okay, this concerns these following words, and then just make make a simple mean over them. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 4 | False | 0.0833 | There is no useful automatic evaluation method for deciding which combined scoring approach is best. | [46:42.35-46:54.11] Speaker B (B): sort of this is going from word to word or it this is going from time to time and then there has to be a way then for you say okay, this concerns these following words, and then just make make a simple mean over them. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 5 | False | 0.1667 | Different annotation methods may operate at different granularities such as words, utterances, time slots, and segments. | [46:42.35-46:54.11] Speaker B (B): sort of this is going from word to word or it this is going from time to time and then there has to be a way then for you say okay, this concerns these following words, and then just make make a simple mean over them. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |

### Context

- Recall: 1/3 (0.3333)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | True | 0.5238 | The meeting is a technical research/planning discussion about annotation data, XML/NITE XML files, segmentation, information density, Rainbow, entropy scoring, and mapping scores back to segments. | # L02 — AMI EN2001b, first 50 minutes [00:30.60-00:34.62] Speaker A (A): It's with cameras You look quite funny at the moment, Tim. [00:42.91-00:45.24] Speaker B (B): This isn't supposed to look like just So the the file with annotations for information density, what would that be like? [35:00.13-35:03.74] Speaker B (B): But like f for now, like your segmentation is just splitting a meeting And then talk about how the annotation for information density and stuff should maybe be structured in a similar way [10:36.48-10:38.57] Speaker B (B): a... | Matched. |
| 2 | False | 0.1818 | The group is trying to understand how to represent and merge multiple annotation outputs into a shared annotation structure. | # L02 — AMI EN2001b, first 50 minutes [00:30.60-00:34.62] Speaker A (A): It's with cameras You look quite funny at the moment, Tim. [00:42.91-00:45.24] Speaker B (B): This isn't supposed to look like just So the the file with annotations for information density, what would that be like? [35:00.13-35:03.74] Speaker B (B): But like f for now, like your segmentation is just splitting a meeting And then talk about how the annotation for information density and stuff should maybe be structured in a similar way [10:36.48-10:38.57] Speaker B (B): a... | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.0 | The discussion is exploratory and technical rather than customer-facing or business-planning oriented. |  | No useful candidate was generated for this expected item. |

## L03 — AMI IN1001 video shot detector technical review

- Category: long
- Score: 0.1
- Expected fixture: `backend/tests/fixtures/meeting_regression/L03_AMI_IN1001_50min.expected.json`
- Actual output: `backend/tests/tmp/meeting_regression_actual/L03_AMI_IN1001_50min.actual.json`

### Decisions

- Recall: 0/7 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.0909 | Use shot-level segmentation as useful output for CINETIS-style restoration or color-correction workflows. | And uh after you can see that indeed because it's a long shot and it's almost like a flat plane, you can do a | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 2 | False | 0.1111 | Use keyframes and shot summaries as a practical way for users to inspect video content. | And uh after you can see that indeed because it's a long shot and it's almost like a flat plane, you can do a | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.2 | Treat motion features as useful for difficult transitions, while recognizing that histogram-based methods can handle many simple cuts. | [09:18.43-09:34.31] Speaker B (B): the this image shows the results using motion when you s use the motion features, and here on the right is when using the histogram uh distance. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 4 | False | 0.1538 | Use the distance output file to retune or reprocess shot thresholds without reprocessing the full video when possible. | [09:18.43-09:34.31] Speaker B (B): the this image shows the results using motion when you s use the motion features, and here on the right is when using the histogram uh distance. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 5 | False | 0.0909 | Keep the frame step parameter at one for shot detection to avoid losing temporal precision. | You have stones and uh so there of course are differences, because on the one hand you have horse, but it's black, so you have more sky, which is black on the right, so you | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 6 | False | 0.2 | Leave the sub-threshold parameter at one. | You have stones and uh so there of course are differences, because on the one hand you have horse, but it's black, so you have more sky, which is black on the right, so you | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 7 | False | 0.0 | Use OpenCV or the MPEG input reader path rather than relying on the old tosh library. |  | No useful candidate was generated for this expected item. |

### Actions

- Recall: 0/5 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.25 | Owner: Speaker B; Action: Provide the shot detector parameter or configuration file discussed at the end of the meeting. | Speaker B [25:00.95-25:02.03] Speaker B (B): who will uh | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 2 | False | 0.3125 | Owner: Speaker B; Action: Help review the C code and video-structure classes if newer versions of the detector are used. | Speaker B [29:46.68-29:47.93] Speaker B (B): will have to check, but if | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 3 | False | 0.325 | Owner: Speaker B; Action: Explain or document how to put video data and XML output into the MMM data workflow. | • # L03 — AMI IN1001, first 50 minutes • Speaker mapping: • - A: Speaker A • - B: Speaker B • - C: Speaker C • - D: Speaker D • [00:33.10-00:33.44] Speaker B (B): Oh yeah. • [00:41.58-00:47.05] Speaker B (B): You don't put your headset microphone? | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 4 | False | 0.25 | Owner: Speaker C; Action: Check whether the DVD/video grabbing issue produced an incorrect or duplicated video file. | • # L03 — AMI IN1001, first 50 minutes • Speaker mapping: • - A: Speaker A • - B: Speaker B • - C: Speaker C • - D: Speaker D • [00:33.10-00:33.44] Speaker B (B): Oh yeah. • [00:41.58-00:47.05] Speaker B (B): You don't put your headset microphone? | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 5 | False | 0.1125 | Owner: Team; Action: Take privacy/password protection into account before exposing experiment videos or MMM browser directories. | But But for and you could imagine that before sending in the D_V_D_, you could allow him to l to watch this type of interface, and | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |

### Risks

- Recall: 0/6 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.0 | Compressed or low-quality video can make visual review harder. |  | No useful candidate was generated for this expected item. |
| 2 | False | 0.0 | Dissolves and ambiguous transitions may not be detected cleanly. |  | No useful candidate was generated for this expected item. |
| 3 | False | 0.0 | Low-texture or black frames reduce the usefulness of motion estimation. |  | No useful candidate was generated for this expected item. |
| 4 | False | 0.1111 | Some libraries or older code may not compile cleanly on Debian. | [46:13.60-46:20.33] Speaker B (B): Yeah, simple things with privacy issues, but uh i there are some methods and everything | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 5 | False | 0.0 | Incorrect video grabbing or cached frames can lead to wrong browser output. |  | No useful candidate was generated for this expected item. |
| 6 | False | 0.25 | Publicly accessible MMM or browser directories can create privacy issues. | [46:13.60-46:20.33] Speaker B (B): Yeah, simple things with privacy issues, but uh i there are some methods and everything | A nearby risk-like candidate exists, but it is not synthesized into the expected risk statement. |

### Context

- Recall: 2/3 (0.6667)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | True | 0.625 | The meeting is a technical status and demo review for a video shot detector. | # L03 — AMI IN1001, first 50 minutes [00:33.10-00:33.44] Speaker B (B): Oh yeah. [00:41.58-00:47.05] Speaker B (B): You don't put your headset microphone? [01:18.01-01:23.36] Speaker A (A): So we are here to just make the point. [02:01.40-02:11.15] Speaker B (B): and the demo, and the goal of uh this meeting is to present the video shot detector to [01:29.64-01:35.08] Speaker A (A): To so you have applied the shot detector to some of the CINETIS video, or [09:34.31-09:59.53] Speaker B (B): the the motion features can better show what's going... | Matched. |
| 2 | True | 0.7 | The goal is to present and explain the video shot detector and review results on CINETIS video data. | # L03 — AMI IN1001, first 50 minutes [00:33.10-00:33.44] Speaker B (B): Oh yeah. [00:41.58-00:47.05] Speaker B (B): You don't put your headset microphone? [01:18.01-01:23.36] Speaker A (A): So we are here to just make the point. [02:01.40-02:11.15] Speaker B (B): and the demo, and the goal of uh this meeting is to present the video shot detector to [01:29.64-01:35.08] Speaker A (A): To so you have applied the shot detector to some of the CINETIS video, or [09:34.31-09:59.53] Speaker B (B): the the motion features can better show what's going... | Matched. |
| 3 | False | 0.3889 | The discussion covers shot detection, keyframe extraction, motion features, histogram distance, Bhattacharya distance, MMM data handling, privacy, and code/library usage. | # L03 — AMI IN1001, first 50 minutes [00:33.10-00:33.44] Speaker B (B): Oh yeah. [00:41.58-00:47.05] Speaker B (B): You don't put your headset microphone? [01:18.01-01:23.36] Speaker A (A): So we are here to just make the point. [02:01.40-02:11.15] Speaker B (B): and the demo, and the goal of uh this meeting is to present the video shot detector to [01:29.64-01:35.08] Speaker A (A): To so you have applied the shot detector to some of the CINETIS video, or [09:34.31-09:59.53] Speaker B (B): the the motion features can better show what's going... | Related evidence exists, but the output does not match the expected item closely enough. |

## L04 — AMI TS3007b degraded functional design meeting for TV remote

- Category: long
- Score: 0.0708
- Expected fixture: `backend/tests/fixtures/meeting_regression/L04_AMI_TS3007b_48min_degraded.expected.json`
- Actual output: `backend/tests/tmp/meeting_regression_actual/L04_AMI_TS3007b_48min_degraded.actual.json`

### Decisions

- Recall: 1/9 (0.1111)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | True | 0.7778 | Keep the remote focused on television use only, not as a general multi-purpose remote. | Uh the remote control shou should onl only be used for the television, so it uh not gonna it's not gonna be a multi-purpose remote control, so uh that's one thing to keep in mind. | Matched. |
| 2 | False | 0.2 | Target the new remote mainly at younger users, especially the sixteen-to-forty-five audience, while keeping it usable for older users. | Mm and some interests from the from the age groups, uh it seems like the young users of remote controls really like the fancy uh new technology stuff, like uh an L_C_D_ screen on the remote control, um speech recognition. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.0833 | Keep the most important controls, especially channel switching, volume, and teletext, clear and easy to access. | Uh second one is also important uh, because it's one of the discussion points of the previous session. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |
| 4 | False | 0.1 | Prioritize simplicity: fewer visible functions, fewer buttons, and important actions available directly. | Uh second one is also important uh, because it's one of the discussion points of the previous session. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 5 | False | 0.0 | Stick primarily with infrared transmission and avoid adding Bluetooth, radio, or a receiver unless cost and compatibility justify it. |  | No useful candidate was generated for this expected item. |
| 6 | False | 0.125 | Avoid overbuilding the remote with too many gadgets or complex functions. | Uh the remote control shou should onl only be used for the television, so it uh not gonna it's not gonna be a multi-purpose remote control, so uh that's one thing to keep in mind. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 7 | False | 0.1538 | Consider touchscreen or LCD-style extra-function areas, but keep primary controls visible and usable. | Uh and uh I think to keep in mind, but not really uh for now is that they uh want the the the slogan and the and the logo uh to uh to be recognised more in the remote. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 8 | False | 0.0 | Use the right-hand design option after the team vote. |  | No useful candidate was generated for this expected item. |
| 9 | False | 0.0909 | Avoid a fragile pop-open or flip-open mechanism because it may be sensitive or easy to break. | Uh second one is also important uh, because it's one of the discussion points of the previous session. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |

### Actions

- Recall: 0/5 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.425 | Owner: Industrial Designer; Action: Take minutes and put updated minutes in the shared folder. | Also Also the minutes of the previous session are also in the shared folder now, so you can read that uh now or afterwards. | A nearby action-like candidate exists, but owner/action phrasing does not match the expected structured action. |
| 2 | False | 0.1571 | Owner: Team; Action: Do another individual-work session after lunch.; Deadline: after lunch | Also Also the minutes of the previous session are also in the shared folder now, so you can read that uh now or afterwards. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.175 | Owner: Team; Action: Use the next email instructions for the next meeting or work session.; Deadline: after lunch | At At the functional design meeting um the plan is uh that uh each one of you, so not me but only you uh will uh present uh the the things you worked on uh the last uh half hour. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 4 | False | 0.1864 | Owner: Team; Action: Save the smartboard or session output into shared/project documents, preferably as an image such as JPEG. | Also Also the minutes of the previous session are also in the shared folder now, so you can read that uh now or afterwards. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 5 | False | 0.05 | Owner: Team; Action: Fill out the questionnaire after lunch.; Deadline: after lunch | At At the functional design meeting um the plan is uh that uh each one of you, so not me but only you uh will uh present uh the the things you worked on uh the last uh half hour. | Very weak lexical/semantic overlap; likely needs higher-level paraphrased synthesis. |

### Risks

- Recall: 0/7 (0.0)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | False | 0.0 | Adding Bluetooth, radio, or a receiver could increase cost and complexity. |  | No useful candidate was generated for this expected item. |
| 2 | False | 0.1 | Relying on TV-screen menus may not work across all televisions. | [27:18.81-27:33.69] Project Manager (B): picks up the remote from the little child and who's all in the systems functions, you'll have to have the possibility to turn off the T_V_ or to switch the channel without um well using all the menu structures to get back to the primary functions. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 3 | False | 0.25 | Too many visible functions or buttons can make the remote hard to use. | [27:18.81-27:33.69] Project Manager (B): picks up the remote from the little child and who's all in the systems functions, you'll have to have the possibility to turn off the T_V_ or to switch the channel without um well using all the menu structures to get back to the primary functions. | A nearby risk-like candidate exists, but it is not synthesized into the expected risk statement. |
| 4 | False | 0.125 | Combining too many functions into one button can confuse users. | [27:18.81-27:33.69] Project Manager (B): picks up the remote from the little child and who's all in the systems functions, you'll have to have the possibility to turn off the T_V_ or to switch the channel without um well using all the menu structures to get back to the primary functions. | Some related evidence exists, but the generated candidate is too literal, incomplete, or noisy. |
| 5 | False | 0.0 | A pop-open or flip-open mechanism may be sensitive or easy to break. |  | No useful candidate was generated for this expected item. |
| 6 | False | 0.0 | A touchscreen or LCD-style design may add cost or implementation complexity. |  | No useful candidate was generated for this expected item. |
| 7 | False | 0.0 | Focusing too much on younger users may reduce usability for older users. |  | No useful candidate was generated for this expected item. |

### Context

- Recall: 1/4 (0.25)

| # | Matched | Score | Expected | Best Candidate | Diagnostic Reason |
|---:|---:|---:|---|---|---|
| 1 | True | 0.8333 | The meeting is a functional design meeting for the remote-control project. | # L04 — AMI TS3007b, first 48 minutes, degraded audio [00:03.59-00:04.31] Marketing Expert (D): Hey guys. [00:04.52-00:06.64] User Interface Designer (C): Hi [00:06.64-00:08.94] User Interface Designer (C): . At the functional design meeting um the plan is uh that uh each one of you, so not me but only you uh will uh present uh the the things you worked on uh the last uh half hour. Third point um that came out of the uh of the questionnaire, uh people used to uh get lost off the remote controller, so maybe it's an idea for us uh to design ex... | Matched. |
| 2 | False | 0.25 | Each participant presents recent individual work and design recommendations. | # L04 — AMI TS3007b, first 48 minutes, degraded audio [00:03.59-00:04.31] Marketing Expert (D): Hey guys. [00:04.52-00:06.64] User Interface Designer (C): Hi [00:06.64-00:08.94] User Interface Designer (C): . At the functional design meeting um the plan is uh that uh each one of you, so not me but only you uh will uh present uh the the things you worked on uh the last uh half hour. Third point um that came out of the uh of the questionnaire, uh people used to uh get lost off the remote controller, so maybe it's an idea for us uh to design ex... | Related evidence exists, but the output does not match the expected item closely enough. |
| 3 | False | 0.2778 | Management guidance says the remote should be TV-only, internet should become the main focus, younger users should be targeted, and the company slogan/logo should be more recognizable on the remote. | # L04 — AMI TS3007b, first 48 minutes, degraded audio [00:03.59-00:04.31] Marketing Expert (D): Hey guys. [00:04.52-00:06.64] User Interface Designer (C): Hi [00:06.64-00:08.94] User Interface Designer (C): . At the functional design meeting um the plan is uh that uh each one of you, so not me but only you uh will uh present uh the the things you worked on uh the last uh half hour. Third point um that came out of the uh of the questionnaire, uh people used to uh get lost off the remote controller, so maybe it's an idea for us uh to design ex... | Related evidence exists, but the output does not match the expected item closely enough. |
| 4 | False | 0.3571 | The audio is degraded, so wording may be imperfect, but the core design direction and follow-up actions should be captured. | # L04 — AMI TS3007b, first 48 minutes, degraded audio [00:03.59-00:04.31] Marketing Expert (D): Hey guys. [00:04.52-00:06.64] User Interface Designer (C): Hi [00:06.64-00:08.94] User Interface Designer (C): . At the functional design meeting um the plan is uh that uh each one of you, so not me but only you uh will uh present uh the the things you worked on uh the last uh half hour. Third point um that came out of the uh of the questionnaire, uh people used to uh get lost off the remote controller, so maybe it's an idea for us uh to design ex... | Related evidence exists, but the output does not match the expected item closely enough. |

## Findings

- The lowest-scoring cases are not failing because of one missing keyword list.
- Many best candidates are raw transcript fragments that are relevant but too literal, partial, or noisy.
- Decisions and risks often require synthesis from several transcript turns, not single-sentence extraction.
- Actions often need owner/action normalization from conversational wording.

## Recommendation

The next quality improvement should focus on a bounded transcript-evidence synthesis layer or summarization prompt refinement, not broader cue expansion.

Recommended next implementation target:

```text
Create a long-meeting synthesis step that converts grouped transcript evidence into clean decisions, actions, risks, and open questions.
```

## Validation Command

```bash
python backend/scripts/run_meeting_regression_baseline.py \
  --case M03 \
  --case L02 \
  --case L03 \
  --case L04 \
  --allow-fail \
  --output backend/tests/tmp/meeting_regression_long_diagnostic_report.json
```
