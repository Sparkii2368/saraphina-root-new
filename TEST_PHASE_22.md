# Test Phase 22: Code Learning System

## Quick Test Guide

### Launch Saraphina
```bash
python "D:\Saraphina Root\saraphina_terminal_ultra.py"
```

---

## Test 1: Learn via Command

```
/learn-code Python classes
```

**Expected Output:**
```
🎓 Learning about: Python classes
   Language: python
   This may take 5-15 seconds...

✅ Learned about Python classes!
   Concept ID: concept_[unique_id]
   Facts stored: 3-5
   Difficulty: 2/4
   Time: ~8000ms

   📚 Prerequisites learned:
      • Object-oriented programming
      • Functions (or similar)

   🔗 Related concepts:
      • Inheritance
      • Polymorphism
      • Methods

   🌳 Recursively learned 1-2 prerequisite concept(s)
```

---

## Test 2: Learn via Natural Language

```
teach me about recursion
```

**Expected Output:**
```
🎓 Learning about recursion...

✅ Just learned about recursion! Stored 4 facts. Also learned 1 prerequisites.

   Use /code-facts recursion to explore details.
```

---

## Test 3: View Concept Details

```
/code-facts Python classes
```

**Expected Output:**
```
📖 Python classes
   Category: paradigm | Difficulty: 2/4
   Language: python
   Confidence: 85% | Used: 1 times

   Description:
   [Full description from GPT-4o]

   💻 Code examples: 2-3 stored

   📚 Prerequisites: [list]

   🔗 Related concepts:
      • [Inheritance, Methods, etc.]

   ID: concept_[id]
   Learned: 2025-11-04 | Last accessed: 2025-11-04
```

---

## Test 4: Expand Knowledge Graph

```
/expand-code concept_[id from above]
```

or

```
/expand-code classes
```

**Expected Output:**
```
🌱 Expanding knowledge from concept...

✅ Expanded from: Python classes
   Learned 2-3 related concept(s)

   📖 [Related concept 1]
      Facts: X | Difficulty: X/4

   📖 [Related concept 2]
      Facts: X | Difficulty: X/4
```

---

## Test 5: Search Concepts

```
/code-facts python
```

**Expected Output:**
```
🔍 Found X matching concepts:

1. Python classes (paradigm, diff: 2/4)
   ID: concept_xxx... | Confidence: 85%
   Language: python

2. Python functions (syntax, diff: 1/4)
   ID: concept_yyy... | Confidence: 85%
   Language: python

[etc.]
```

---

## Test 6: Multiple Natural Language Variants

Try these:
- `what are Python decorators?`
- `explain async/await`
- `how does inheritance work?`
- `tell me about lambdas in Python`
- `learn about JavaScript promises`

All should trigger code learning!

---

## Verify Database

After learning, check the database:

```sql
SELECT COUNT(*) FROM code_concepts;
-- Should show concepts learned

SELECT COUNT(*) FROM code_snippets;
-- Should show code examples

SELECT COUNT(*) FROM concept_links;
-- Should show relationships

SELECT * FROM code_learning_log ORDER BY created_at DESC LIMIT 5;
-- Should show recent learning events
```

---

## Expected Behavior

### ✅ Success Indicators:
- GPT-4o queries complete in 5-15 seconds
- Concepts stored with all metadata
- Prerequisites learned recursively (up to depth 3)
- Related concepts linked in graph
- Code examples extracted and stored
- Natural language triggers work
- No errors or crashes

### ⚠️ Known Behaviors:
- First query to GPT-4o may be slower (~10-15s)
- Already-learned concepts return instant "already known" message
- Some prerequisites may not have prerequisites themselves
- Related concepts are linked but not auto-learned (use `/expand-code` for that)

---

## Troubleshooting

**If you see "GPT-4o not available":**
- Check `OPENAI_API_KEY` is set in .env
- Verify API key is valid
- Run: `python "D:\Saraphina Root\test_gpt4_connection.py"`

**If learning fails:**
- Check internet connection
- Verify GPT-4o API access (not all keys have GPT-4o)
- Check logs for specific error

**If natural language doesn't trigger:**
- Make sure query contains programming keywords (python, class, function, etc.)
- Try explicit command: `/learn-code [concept]`

---

## Success Checklist

- [ ] `/learn-code Python classes` works
- [ ] Natural language "teach me about recursion" works
- [ ] `/code-facts [concept]` shows details
- [ ] `/expand-code [id]` learns related concepts
- [ ] Multiple concepts can be learned in sequence
- [ ] Already-learned concepts return "already know" message
- [ ] Prerequisites are learned recursively
- [ ] Database tables populated correctly

---

## Ready for Phase 23!

Once all tests pass, Saraphina has a working code knowledge base and is ready to move to **Phase 23: Self-Modification** where she'll start proposing and testing code changes to improve herself! 🚀
