# | Details | Hackaday.io (web page)

Source: https://www.hackaday.io/project/181875-open6x-robot-arm/details · licence: unknown (check before copying)

| What | Where |
|---|---|
| Source metadata | inspiration/hackaday-project-181875-open6x-robot-arm-details/source.json |
| Page text (html.parser) | inspiration/hackaday-project-181875-open6x-robot-arm-details/page.txt |
| Images (6, EXIF-free) | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/ |

## Images
| # | Image | Alt text | Shows |
|---|---|---|---|
| 1 | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/01.jpg | og:image | TODO(research) |
| 2 | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/02.jpg |  | TODO(research) |
| 3 | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/03.jpg |  | TODO(research) |
| 4 | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/04.jpg |  | TODO(research) |
| 5 | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/05.jpg |  | TODO(research) |
| 6 | inspiration/hackaday-project-181875-open6x-robot-arm-details/images/06.jpg |  | TODO(research) |

## Mechanism mentions (page text)
Counts: stepper 22, nema 15, belt 12, pulley 12, gear 8, planetary 8, bearing 3, motor 3.
- "The initial release of this robot arm used stepper motors to directly drive toothed belts at the joints. In this first revision, 3D printed ..."
- "Motor holding torque Planetary gear reduction Belt drive reduction"
- "Atthe base link (see image above), a Nema 17-40 stepper with a planetary gear reducer actuates a belt driving a pulley fixed to the ..."
- "... shoulder link (see image above) holds the two Nema 23 steppers, each fixed to its own bracket, one placed on top of the ..."

## Embedded videos (digest each with `mechy intake add <url>`)
- https://www.youtube.com/watch?v=1A0QFTGBgz8
- https://www.youtube.com/watch?v=gBgTcezkIw8
- https://www.youtube.com/watch?v=4p3Nld00_x0
- https://www.youtube.com/watch?v=pzzVH0w-LhQ

## Research notes
- Mechanism and layout: 6-axis serial arm, ~500 mm reach.
- Actuators, transmission, bearings, specs (cite timestamps/frames): J2 NEMA23 with 4:1 printed planetary x 5:1 HTD-3M = 20:1; Mega + RAMPS + DRV8825/DM556; 0.5 kg tested near full extension.
- Copy / avoid for this project: Lesson: a driver burned at 0.5 kg; keep A4988 current at or below ~1 A with heatsinks and a fan.

Not verified: machine-made digest; page text is extracted automatically and claims on it are unchecked.
