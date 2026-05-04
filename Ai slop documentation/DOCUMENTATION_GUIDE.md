# 📚 Documentation Navigation Guide

Welcome! This repository contains comprehensive documentation for the GECCO Framsticks Competition. Use this guide to find what you need.

---

## 🎯 Quick Start (5 minutes)

**You just want to start coding?** Read these in order:

1. **[IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md)** (This is where you start!)
   - Step-by-step setup instructions
   - Ready-to-use example algorithm
   - Testing procedures
   - Submission checklist

2. **Run the example algorithm** provided in that file
3. **Modify it** for your optimization strategy
4. **Test locally** before submitting

---

## 📖 Complete Documentation Map

### For Understanding the Competition

| Document | Purpose | Reading Time |
|----------|---------|---|
| [README.md](README.md) | Complete competition overview, requirements, evaluation criteria | 15 min |
| [FRAMSTICKS_LIB_COMPETITION_GUIDE.md](FRAMSTICKS_LIB_COMPETITION_GUIDE.md) | Deep dive into the `FramsticksLibCompetition` class, what it does and how to use it | 20 min |
| [FRAMSTICKS_REFERENCE_VISUAL.md](FRAMSTICKS_REFERENCE_VISUAL.md) | Technical reference with diagrams, code examples, and class structure | 25 min |

### For Implementation

| Document | Purpose | Reading Time |
|----------|---------|---|
| [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) | Practical step-by-step guide to building your algorithm | 30 min |
| Example code in Quick Start | Working example you can copy and modify | 10 min |

---

## 🗺️ Choose Your Path

### Path 1: "Just Show Me How to Code" (30 min)
1. Open [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md)
2. Follow Step 1-3 (understanding + setup)
3. Copy the algorithm code from Step 3
4. Test it with Step 4
5. Start optimizing your algorithm

### Path 2: "I Need to Understand Everything" (2 hours)
1. Read [README.md](README.md) — Competition overview
2. Read [FRAMSTICKS_LIB_COMPETITION_GUIDE.md](FRAMSTICKS_LIB_COMPETITION_GUIDE.md) — Technical details
3. Read [FRAMSTICKS_REFERENCE_VISUAL.md](FRAMSTICKS_REFERENCE_VISUAL.md) — Deep reference
4. Read [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) — Practical guide
5. Code and test

### Path 3: "I Already Know Evolutionary Algorithms" (45 min)
1. Skim [README.md](README.md) — Get the competition specifics
2. Read [FRAMSTICKS_LIB_COMPETITION_GUIDE.md](FRAMSTICKS_LIB_COMPETITION_GUIDE.md) — Understand the API
3. Jump to [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) Step 2-7
4. Code with your own strategy

### Path 4: "I'm Stuck or Debugging" (varies)
1. Check FAQ section in [README.md](README.md)
2. See "Common Mistakes" in [FRAMSTICKS_REFERENCE_VISUAL.md](FRAMSTICKS_REFERENCE_VISUAL.md)
3. Read "Debugging Tips" in [FRAMSTICKS_LIB_COMPETITION_GUIDE.md](FRAMSTICKS_LIB_COMPETITION_GUIDE.md)
4. Check "Troubleshooting" in [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md)

---

## 📌 Quick Reference by Topic

### "How do I...?"

#### ...get started?
→ [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md), Steps 1-3

#### ...understand the competition task?
→ [README.md](README.md), "Core Task" section

#### ...know what to implement?
→ [FRAMSTICKS_LIB_COMPETITION_GUIDE.md](FRAMSTICKS_LIB_COMPETITION_GUIDE.md), "How It Evaluates COG Movement"

#### ...set up my environment?
→ [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md), Step 2

#### ...create an algorithm?
→ [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md), Step 3 (with code)

#### ...test my algorithm?
→ [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md), Step 4

#### ...optimize my algorithm?
→ [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md), Step 6

#### ...submit?
→ [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md), Step 5

#### ...use the FramsticksLibCompetition API?
→ [FRAMSTICKS_REFERENCE_VISUAL.md](FRAMSTICKS_REFERENCE_VISUAL.md), "Methods Reference" section

#### ...understand fitness values?
→ [FRAMSTICKS_LIB_COMPETITION_GUIDE.md](FRAMSTICKS_LIB_COMPETITION_GUIDE.md), "Return Value Formats" section

#### ...handle time/evaluation limits?
→ [FRAMSTICKS_REFERENCE_VISUAL.md](FRAMSTICKS_REFERENCE_VISUAL.md), "Time Accounting" section

#### ...debug a problem?
→ Check "Troubleshooting" in [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md)

---

## 📊 What Each Document Contains

### README.md
**Purpose**: Official competition requirements and overview

**Contains**:
- Competition goal and overview
- Evaluation criteria (how winners are determined)
- 10 settings and constraints
- Resource limits (time, memory, evaluations)
- Technical reference for FramsticksLibCompetition
- Submission requirements
- Getting started guide
- Previous competition results
- FAQ

**Use when**: You need the "big picture" or official requirements

---

### FRAMSTICKS_LIB_COMPETITION_GUIDE.md
**Purpose**: Technical deep-dive into the competition API

**Contains**:
- Class structure and inheritance
- Configuration options (COMPETITOR_ID, FITNESS_FORMAT, etc.)
- Method signatures and return values
- Automatic limit checking behavior
- Time tracking explanation
- How COG movement is evaluated (TEST_FUNCTION 3/4/5)
- Typical algorithm loop pattern
- Debugging tips
- Performance considerations

**Use when**: You need to understand how FramsticksLibCompetition works

---

### FRAMSTICKS_REFERENCE_VISUAL.md
**Purpose**: Visual technical reference with diagrams and examples

**Contains**:
- Class hierarchy diagram
- Data flow diagram
- Fitness computation pipeline
- Detailed method reference with examples
- Time accounting diagram
- Evaluation budget breakdown
- Common mistakes and solutions
- Best practices
- Code examples for all methods
- When to use what

**Use when**: You want visual explanations or code examples

---

### IMPLEMENTATION_QUICK_START.md
**Purpose**: Practical, step-by-step implementation guide

**Contains**:
- Task understanding (5 min read)
- Environment setup instructions
- Complete working example algorithm (you can copy this!)
- How to test your algorithm
- How to prepare submission files
- How to optimize your algorithm
- Final submission checklist
- Troubleshooting guide

**Use when**: You're ready to code and need practical guidance

---

## 🎓 Recommended Reading Order

### For First-Time Participants
```
1. README.md (15 min)
   ↓ Understand what you're building
2. IMPLEMENTATION_QUICK_START.md (30 min)
   ↓ See the big picture and get coding
3. FRAMSTICKS_LIB_COMPETITION_GUIDE.md (20 min)
   ↓ Understand the API in detail
4. FRAMSTICKS_REFERENCE_VISUAL.md (25 min)
   ↓ Reference as needed while coding
```

### For Experienced Programmers
```
1. README.md (skim, 5 min)
   ↓ Get competition specifics
2. FRAMSTICKS_LIB_COMPETITION_GUIDE.md (15 min)
   ↓ Understand the API
3. IMPLEMENTATION_QUICK_START.md (Step 3 only, 10 min)
   ↓ Copy example code
4. Code your own strategy
5. FRAMSTICKS_REFERENCE_VISUAL.md (reference while debugging)
```

---

## 📁 File Contents Quick Reference

```
Repository
├── README.md
│   └─ Complete competition info (official)
│
├── FRAMSTICKS_LIB_COMPETITION_GUIDE.md
│   └─ Technical API documentation
│
├── FRAMSTICKS_REFERENCE_VISUAL.md
│   └─ Visual guide with diagrams and examples
│
├── IMPLEMENTATION_QUICK_START.md
│   └─ Step-by-step implementation guide (START HERE!)
│
├── DOCUMENTATION_GUIDE.md (← you are here)
│   └─ Navigation and reading guide
│
├── FramsticksEvolution.py
│   └─ Example algorithm (DEAP-based, reference only)
│
└── [Your Files Here]
    ├── my_algorithm.py
    ├── requirements.txt
    └── README.txt
```

---

## 💡 Quick Tips

- **Stuck?** → Check "Troubleshooting" in IMPLEMENTATION_QUICK_START.md
- **Confused about API?** → Jump to FRAMSTICKS_REFERENCE_VISUAL.md "Methods Reference"
- **Want code examples?** → FRAMSTICKS_REFERENCE_VISUAL.md has tons of them
- **Ready to code?** → Copy algorithm from IMPLEMENTATION_QUICK_START.md Step 3
- **Need official requirements?** → See README.md
- **Unsure about a concept?** → Use the Table of Contents in each document

---

## ⏱️ Time Investment

| Goal | Time | Path |
|------|------|------|
| **Get working code** | 30 min | Quick Start Path |
| **Understand everything** | 2 hours | Comprehensive Path |
| **Implement optimized algorithm** | 4-8 hours | Implement → Iterate → Optimize |
| **Compete seriously** | 20+ hours | Full competition prep |

---

## 🎯 Checkpoints

### Before You Start Coding
- [ ] Read at least IMPLEMENTATION_QUICK_START.md Step 1
- [ ] Understand "Core Task" from README.md
- [ ] Know what evaluation limits are (100k evals, 1 hour)

### Before You Run Code
- [ ] Environment is set up (Python, Framsticks, framspy)
- [ ] Framsticks library path is known
- [ ] You can run `python frams-test.py <path>`

### Before You Submit
- [ ] Algorithm runs locally without errors
- [ ] Works in a clean directory (no dev dependencies)
- [ ] Calls `frams_lib.end()` at the end
- [ ] All files are in submission.zip
- [ ] README.txt has clear instructions
- [ ] Email deadline: June 15, 2026

---

## 🔗 Related Resources

**Official**:
- [Framsticks.com](https://www.framsticks.com/)
- [GECCO Competition Page](https://www.framsticks.com/gecco-competition)
- Contact: support@framsticks.com

**Libraries**:
- [DEAP Framework](https://deap.readthedocs.io/)
- [NumPy Documentation](https://numpy.org/doc/)

**Previous Results**:
- Check README.md for links to 2024/2025 results

---

## 📝 Document Legend

Throughout the documentation, you'll see:

| Symbol | Meaning |
|--------|---------|
| ✅ | Do this / Good practice |
| ❌ | Don't do this / Common mistake |
| ⚠️ | Warning / Important |
| 📌 | Key point / Remember this |
| 💡 | Tip / Helpful hint |
| 🔗 | Link / Reference |
| 📖 | Additional reading |

---

## 🚀 Next Steps

1. **If you haven't started**: Open [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) and begin at Step 1

2. **If you're setting up**: Follow [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) Steps 2-4

3. **If you're coding**: Keep [FRAMSTICKS_REFERENCE_VISUAL.md](FRAMSTICKS_REFERENCE_VISUAL.md) open for API reference

4. **If you're debugging**: Check "Troubleshooting" in [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md)

5. **If you're ready to submit**: Follow [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) Step 5-7

---

## ❓ FAQ About This Documentation

**Q: Which document should I read first?**  
A: [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) if you want to code immediately, or [README.md](README.md) if you want full context first.

**Q: Can I just read one document?**  
A: Yes, [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) is self-contained with an example.

**Q: Are these documents official?**  
A: [README.md](README.md) contains official competition requirements. The other documents are reference guides created from that.

**Q: Where's the official spec?**  
A: In [README.md](README.md), under "Scope" and "Judging" sections.

**Q: How do I submit?**  
A: See [IMPLEMENTATION_QUICK_START.md](IMPLEMENTATION_QUICK_START.md) Step 5 and [README.md](README.md) "Submission Requirements".

**Q: When is the deadline?**  
A: June 15, 2026 (stated in [README.md](README.md))

---

## 🎓 Document Philosophy

These documents were created to:
1. **Make competition accessible** to developers at all levels
2. **Provide clear examples** with working code
3. **Explain the "why"** not just the "how"
4. **Offer multiple entry points** (quick start, deep dive, reference)
5. **Gather information** from scattered official sources

Think of them as:
- **README.md** = "What and why"
- **FRAMSTICKS_LIB_COMPETITION_GUIDE.md** = "Technical how"
- **FRAMSTICKS_REFERENCE_VISUAL.md** = "API reference with examples"
- **IMPLEMENTATION_QUICK_START.md** = "Practical step-by-step"

Good luck with your submission! 🚀

---

*Last updated: 2026*  
*For the latest official information, visit https://www.framsticks.com/gecco-competition*
