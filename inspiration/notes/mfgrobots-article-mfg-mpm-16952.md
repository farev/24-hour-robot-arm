# Build Your Own MK2 Plus Robot Arm Controller (web page)

Source: https://www.mfgrobots.com/Article/mfg/mpm/16952.html · licence: unknown (check before copying)

| What | Where |
|---|---|
| Source metadata | inspiration/mfgrobots-article-mfg-mpm-16952/source.json |
| Page text (html.parser) | inspiration/mfgrobots-article-mfg-mpm-16952/page.txt |
| Images (6, EXIF-free) | inspiration/mfgrobots-article-mfg-mpm-16952/images/ |

## Images
| # | Image | Alt text | Shows |
|---|---|---|---|
| 1 | inspiration/mfgrobots-article-mfg-mpm-16952/images/01.png | Build Your Own MK2 Plus Robot ... | TODO(research) |
| 2 | inspiration/mfgrobots-article-mfg-mpm-16952/images/02.jpg | Build Your Own MK2 Plus Robot ... | TODO(research) |
| 3 | inspiration/mfgrobots-article-mfg-mpm-16952/images/03.jpg | Build Your Own MK2 Plus Robot ... | TODO(research) |
| 4 | inspiration/mfgrobots-article-mfg-mpm-16952/images/04.jpg | Build Your Own MK2 Plus Robot ... | TODO(research) |
| 5 | inspiration/mfgrobots-article-mfg-mpm-16952/images/05.jpg | Build Your Own MK2 Plus Robot ... | TODO(research) |
| 6 | inspiration/mfgrobots-article-mfg-mpm-16952/images/06.jpg | Build Your Own MK2 Plus Robot ... | TODO(research) |

## Mechanism mentions (page text)
Counts: stepper 44, motor 26, linkage 4, servo 4, nema 2.
- "OpenBuilds NEMA 17 Stepper Motor I used generic Nema 17 Steppers. SparkFun Stepper motor driver board A4988"
- "... by the brilliant daghizmo ) shares the kinematic linkage of the ABB IRB460 scaled down with a ratio of 1:7. However, this arm ..."
- "Unlike servos, stepper motors don't have any positional awareness. We'll have to remedy this by first setting up a homing routine when the arm ..."

## Research notes
- Mechanism and layout: EEZYbotARM MK2 Plus: ABB IRB460-style linkage scaled up, stepper conversion.
- Actuators, transmission, bearings, specs (cite timestamps/frames): 3x NEMA17, Uno + CNC shield + A4988, AccelStepper, 3 limit switches, 12 V.
- Copy / avoid for this project: Same electronics as ours. Lesson: wrong homing direction / reversed A4988 destroys drivers; add soft limits and a homing timeout, first power-up unloaded.

Not verified: machine-made digest; page text is extracted automatically and claims on it are unchecked.
