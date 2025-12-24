# WAN 2.2 Image-to-Video Camera Movement Prompts

> **Purpose:** Camera-only movements with minimal/no subject motion
> **Mode:** Image-to-Video (I2V)
> **Model:** WAN 2.2

---

## Quick Reference

| Camera Movement | CFG Range | Difficulty |
|-----------------|-----------|------------|
| Pan Left        | 7-8       | Easy       |
| Pan Right       | 7-8       | Easy       |
| Dolly In        | 7-9       | Medium     |
| Dolly Out       | 7-9       | Medium     |
| Rotate Left     | 8-9       | Medium     |
| Rotate Right    | 8-9       | Medium     |
| Orbit 360       | 8-10      | Hard       |

---

## Pan Left

### Positive Prompt
```
Static shot, the camera pans slowly to the left, fixed subject, no movement, still scene, locked composition, smooth horizontal camera motion, maintaining exact pose from reference image, frozen pose, stationary elements, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, walking, running, moving objects, animation, dynamic action, body movement, facial movement, blinking, swaying, wind motion, pose change, gesture change
```

### Recommended CFG: `7-8`

---

## Pan Right

### Positive Prompt
```
Static shot, the camera pans slowly to the right, fixed subject, no movement, frozen scene, stationary elements, smooth horizontal tracking, maintaining exact pose from reference image, locked composition, still subject, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, walking, running, moving objects, animation, dynamic action, body movement, facial movement, blinking, swaying, wind motion, pose change, gesture change
```

### Recommended CFG: `7-8`

---

## Dolly In (Push In)

### Positive Prompt
```
Static shot, the camera slowly pushes in, dolly in, fixed subject, no movement, frozen pose, stationary scene, smooth forward camera motion, maintaining exact pose from reference image, locked subject position, still elements, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, walking, approaching camera, moving objects, animation, dynamic action, body movement, facial expression change, breathing motion, pose change, leaning forward
```

### Recommended CFG: `7-9`

---

## Dolly Out (Pull Back)

### Positive Prompt
```
Static shot, the camera slowly pulls back, dolly out, fixed subject, no movement, frozen scene, stationary elements, revealing shot, smooth backward camera motion, maintaining exact pose from reference image, locked composition, still subject, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, walking away, receding motion, moving objects, animation, dynamic action, body movement, facial movement, pose change, shrinking subject
```

### Recommended CFG: `7-9`

---

## Rotate Left (Counter-Clockwise Roll)

### Positive Prompt
```
Static shot, camera rotates counterclockwise, roll left, fixed subject, no movement, frozen scene, stationary elements, Dutch angle transition, maintaining exact pose from reference image, locked subject position, still composition, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, spinning subject, rotating objects, moving elements, animation, dynamic action, body movement, swaying, tilting, leaning, pose change
```

### Recommended CFG: `8-9`

---

## Rotate Right (Clockwise Roll)

### Positive Prompt
```
Static shot, camera rotates clockwise, roll right, fixed subject, no movement, frozen scene, stationary elements, Dutch angle transition, maintaining exact pose from reference image, locked subject position, still composition, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, spinning subject, rotating objects, moving elements, animation, dynamic action, body movement, swaying, tilting, leaning, pose change
```

### Recommended CFG: `8-9`

---

## Orbit 360 / Arc Shot

### Positive Prompt
```
Static subject, arc shot, camera orbits around the subject 360 degrees, fixed pose, no movement, frozen scene, stationary subject, smooth circular camera motion, center composition, maintaining exact pose from reference image, locked subject position, absolutely still subject, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, turning head, following camera, rotating subject, moving objects, animation, dynamic action, body movement, facial tracking, eye movement, pose change, subject rotation, head tracking
```

### Recommended CFG: `8-10`

---

## Pro Tips

### 1. Reinforce Stillness
Add these terms to strengthen subject lock:
- `"frozen in place"`
- `"statue-like stillness"`
- `"completely motionless"`
- `"time-frozen subject"`

### 2. Speed Control
Prefix camera movements with speed modifiers:
- `"very slowly"` - Minimal dynamics
- `"slowly"` - Standard smooth motion
- `"gradually"` - Gentle progression

### 3. For Product/Object Shots
Add to positive prompt:
```
product photography, still life, studio shot, fixed object
```

### 4. For Character/Person Shots
Add to positive prompt:
```
portrait photography, frozen expression, held pose, mannequin-like stillness
```

### 5. For Documentary/Cinematic Scenes
Add to positive prompt:
```
documentary style, observational camera, non-reactive subject
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Subject still moving slightly | Increase CFG by 1-2 points |
| Camera movement too fast | Add "very slowly" to prompt |
| Unnatural frozen look | Reduce CFG slightly, accept minimal motion |
| Subject tracking camera | Add "non-reactive subject, ignoring camera" to positive |
| Background elements moving | Add "static background, frozen environment" to positive |

---

## Example: Cybercrime Documentary Style

For dark web / cybercrime documentary visuals:

### Positive Prompt (Dolly In Example)
```
Static shot, the camera slowly pushes in, dolly in, fixed subject, no movement, frozen pose, stationary scene, smooth forward camera motion, maintaining exact pose from reference image, locked subject position, dark atmospheric lighting, moody shadows, cyberpunk aesthetic, hacker environment, computer screens glowing, cinematic, photorealistic
```

### Negative Prompt
```
subject movement, character motion, typing, moving hands, head movement, animation, dynamic action, body movement, facial expression change, breathing motion, pose change, screen flickering
```

### CFG: `8-9`

---

## Copy-Paste Templates

### Minimal Template (Any Camera Movement)
```
Positive: Static shot, [CAMERA MOVEMENT], fixed subject, no movement, maintaining exact pose from reference image, frozen scene, cinematic, photorealistic

Negative: subject movement, character motion, moving objects, animation, dynamic action, body movement, pose change
```

### Maximum Lock Template (Any Camera Movement)
```
Positive: Static shot, [CAMERA MOVEMENT], fixed subject, absolutely no movement, maintaining exact pose from reference image, frozen in place, statue-like stillness, time-frozen subject, locked composition, completely motionless, cinematic, photorealistic

Negative: subject movement, character motion, walking, running, moving objects, animation, dynamic action, body movement, facial movement, blinking, swaying, wind motion, pose change, gesture change, breathing, micro-movements, any motion
```

---

*Document created for WAN 2.2 I2V workflows*
*Last updated: December 2024*
