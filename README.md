# Spooky_Halloween_Music_Generater
A **spooky step sequencer** built with `pygame` and `pygame_gui`, where you can create drum patterns, adjust tempo, and remix your beats into a **Halloween-themed track** complete with background music and visuals.

---

## 🧩 Features
- 🎵 **3 Instruments** — Bass Drum, Snare, and Hi-Hat  
- ⚙️ **8-Step Sequencer Grid** — toggle beats easily  
- ⏱️ **Tempo Control** — adjustable via slider *and* text input  
- ▶️ **Play / Stop Buttons** — control playback in real-time  
- 🎃 **“Convert to Halloween Song”** — mixes your beats with a spooky background melody  
- 🛑 **Stop Halloween Track** — stop the generated Halloween song instantly  
- 🌆 **Halloween Background Image** — themed visuals for the season  

---

## 🧰 Requirements

Install these Python packages:
```bash
pip install pygame==2.1.3 pygame_gui==0.6.0
```

> ⚠️ Newer versions of pygame (like 2.6.x) currently break pygame_gui, so stick to these versions.

---

## 📁 Project Structure

```
HalloweenSequencer/
├── main.py                     # main program file (your current script)
├── sounds/
│   ├── bass.wav
│   ├── snare.wav
│   ├── hihat.wav
│   └── spooky_melody.wav
├── images/
│   └── halloween_bg.jpg
└── README.md
```

---

## 🕹️ How to Run
1. Clone or download this repository.  
2. Make sure your folder includes the `sounds` and `images` directories.  
3. Run the program:
   ```bash
   python main.py
   ```
4. Build your beat using the grid:
   - Click boxes to activate/deactivate beats.  
   - Adjust **tempo** using the slider or text box.  
   - Press **Play** to start playback.  
   - Press **Convert to Halloween Song** for a spooky remix.  
   - Use **Stop Halloween Track** to end it early.  

---

## 🧠 Technical Notes
- The Halloween remix plays for **16 full loops**, then automatically stops.  
- The spooky background melody plays in a **loop** while the remix runs.  
- The app uses **multithreading** to prevent freezing during playback.  

---

## 🕷️ Troubleshooting

| Problem | Solution |
|----------|-----------|
| `ImportError: cannot import name 'DIRECTION_LTR' from 'pygame'` | Downgrade to `pygame==2.1.3` |
| App freezes when playing | Ensure threading edits are applied and you’re not using `time.sleep()` directly |
| Sounds not playing | Check `.wav` file paths and make sure mixer is initialized |

---

## 🧛 Credits
- Built with 💀 **pygame** + **pygame_gui**  
- Developed by *Shivam Himatsingka & Naman Kedia & ChatGPT (GPT-5)*  
- Background art and sound effects — royalty-free from [Pixabay](https://pixabay.com) & [Freesound](https://freesound.org)
