# Nexa Board-Style Teaching System

## Overview

Nexa now teaches like a real classroom teacher writing on a board. The AI uses structured, step-by-step explanations with proper mathematical formatting to create an authentic learning experience.

## Key Features

### 1. ✅ Board-Style Formatting
Responses are structured like a teacher writing on a classroom board:
- Clear step markers (Step 1, Step 2, etc.)
- One logical operation per step
- Visual progression through the solution
- Proper mathematical notation using LaTeX

### 2. ✅ Streamed Presentation
Solutions appear gradually, not all at once:
- Step 1 appears first
- Then Step 2
- Then Step 3
- Creates the feeling of watching a teacher solve in real-time

### 3. ✅ Professional Math Formatting
All mathematical expressions use LaTeX for beautiful rendering:
- Fractions: `$\frac{1}{2}$` → ½
- Powers: `$x^2$` → x²
- Square roots: `$\sqrt{16}$` → √16
- Equations: `$2x + 5 = 15$` → 2x + 5 = 15

## Teaching Structure

### Standard Problem-Solving Format

```
Problem: [State the problem clearly]

Step 1
[First operation with proper formatting]

Step 2
[Second operation with proper formatting]

Step 3
[Third operation with proper formatting]

Final Answer: [Clear, formatted answer]
```

### Example: Solving a Fraction Addition

**Student asks:** "How do I add 1/2 + 1/3?"

**Nexa responds:**

```
Problem: Solve $\frac{1}{2} + \frac{1}{3}$

Step 1
Write the fractions:
$$\frac{1}{2} + \frac{1}{3}$$

Step 2
Find the LCM of 2 and 3
LCM(2,3) = 6

Step 3
Convert to common denominator:
$$\frac{3}{6} + \frac{2}{6}$$

Step 4
Add the numerators:
$$\frac{5}{6}$$

Final Answer: $\frac{5}{6}$

Does this make sense? Can you try adding $\frac{1}{4} + \frac{1}{6}$ on your own?
```

## Learning Modes with Board Style

### 📖 Explain Mode (Board Tutor Style)

**Characteristics:**
- Detailed step-by-step explanations
- Shows all work like a teacher on a board
- Includes understanding checks
- Uses analogies and examples

**Example Response:**
```
Let's solve this together!

Problem: Solve $2x + 5 = 15$

Step 1: Write the equation
$$2x + 5 = 15$$

Step 2: Subtract 5 from both sides
$$2x + 5 - 5 = 15 - 5$$
$$2x = 10$$

Step 3: Divide both sides by 2
$$\frac{2x}{2} = \frac{10}{2}$$
$$x = 5$$

Step 4: Verify the answer
$$2(5) + 5 = 10 + 5 = 15$$ ✓

Final Answer: $x = 5$

Does that make sense? Notice how we performed the same operation on both sides to keep the equation balanced.
```

### 🎯 Coach Mode (Guided Discovery)

**Characteristics:**
- Asks guiding questions
- Provides hints with proper formatting
- Encourages student to think
- Reveals solution gradually

**Example Response:**
```
Great question! Let's work through this together.

Problem: Solve $2x + 5 = 15$

Before I show you, let me ask:
- What do you think we should do first to isolate $x$?
- What operation is being done to $x$ right now?

Hint: Look at the equation $2x + 5 = 15$
We want to get $x$ by itself. What's "attached" to $x$?

[If student needs more help]

Step 1: We need to remove the +5
Subtract 5 from both sides:
$$2x = 10$$

Now, what should we do next to get $x$ alone?
```

### 📝 Exam Mode (Direct Solutions)

**Characteristics:**
- Concise, efficient solutions
- All steps shown clearly
- Direct answers
- Proper formatting maintained

**Example Response:**
```
Problem: Solve $2x + 5 = 15$

Solution:
Step 1: Subtract 5 from both sides
$$2x = 10$$

Step 2: Divide by 2
$$x = 5$$

Final Answer: $x = 5$
```

## Visual Teaching Elements

### Text Diagrams

For geometry and visual concepts:

```
Triangle ABC
    A
   / \
  /   \
 B-----C

Right Triangle
    |\ 
  a | \ c
    |  \
    |___\
      b
```

### Number Lines

```
-3  -2  -1   0   1   2   3
 |---|---|---|---|---|---|
         ←---x--->
```

### Coordinate Systems

```
    y
    |
  2 |     • (2,3)
  1 |
----+----→ x
 -1 |
    |
```

## LaTeX Formatting Guide

### Basic Math Expressions

| Type | LaTeX | Renders As |
|------|-------|------------|
| Fraction | `$\frac{1}{2}$` | ½ |
| Power | `$x^2$` | x² |
| Subscript | `$x_1$` | x₁ |
| Square root | `$\sqrt{16}$` | √16 |
| Nth root | `$\sqrt[3]{8}$` | ³√8 |

### Complex Expressions

| Type | LaTeX | Description |
|------|-------|-------------|
| Quadratic | `$ax^2 + bx + c = 0$` | Standard form |
| Summation | `$\sum_{i=1}^{n} i$` | Sum notation |
| Integral | `$\int_0^1 x dx$` | Definite integral |
| Limit | `$\lim_{x \to 0} f(x)$` | Limit notation |

### Display vs Inline Math

**Inline math** (within text): `$x = 5$`
- Use single dollar signs
- Appears in the flow of text

**Display math** (centered, standalone): `$$x = 5$$`
- Use double dollar signs
- Appears centered on its own line
- Better for important equations

## Step-by-Step Best Practices

### ✅ DO:

1. **One operation per step**
   ```
   Step 1: Subtract 5
   Step 2: Divide by 2
   ```

2. **Show intermediate results**
   ```
   Step 1: $2x + 5 = 15$
   Step 2: $2x = 10$
   Step 3: $x = 5$
   ```

3. **Use clear step markers**
   ```
   Step 1
   Step 2
   Step 3
   ```

4. **Include understanding checks**
   ```
   Does this make sense?
   Can you see why we did that?
   Try this similar problem...
   ```

### ❌ DON'T:

1. **Don't combine multiple operations**
   ```
   ❌ Step 1: Subtract 5 and divide by 2
   ✅ Step 1: Subtract 5
   ✅ Step 2: Divide by 2
   ```

2. **Don't skip steps**
   ```
   ❌ $2x + 5 = 15$ → $x = 5$
   ✅ Show all intermediate steps
   ```

3. **Don't use raw symbols**
   ```
   ❌ 1/2 + 1/3
   ✅ $\frac{1}{2} + \frac{1}{3}$
   ```

4. **Don't dump large blocks of text**
   ```
   ❌ Long paragraph explaining everything at once
   ✅ Break into clear steps with formatting
   ```

## Subject-Specific Examples

### Mathematics

```
Problem: Factor $x^2 + 5x + 6$

Step 1: Identify the form
This is a quadratic: $ax^2 + bx + c$
Where $a=1$, $b=5$, $c=6$

Step 2: Find two numbers that:
- Multiply to give $c = 6$
- Add to give $b = 5$

Numbers: 2 and 3
- $2 \times 3 = 6$ ✓
- $2 + 3 = 5$ ✓

Step 3: Write as factors
$$x^2 + 5x + 6 = (x + 2)(x + 3)$$

Final Answer: $(x + 2)(x + 3)$
```

### Physics

```
Problem: Calculate velocity from $v = u + at$
Given: $u = 5$ m/s, $a = 2$ m/s², $t = 3$ s

Step 1: Write the formula
$$v = u + at$$

Step 2: Substitute values
$$v = 5 + (2)(3)$$

Step 3: Calculate
$$v = 5 + 6$$
$$v = 11$$

Final Answer: $v = 11$ m/s
```

### Chemistry

```
Problem: Balance the equation
$H_2 + O_2 → H_2O$

Step 1: Count atoms on each side
Left: H=2, O=2
Right: H=2, O=1

Step 2: Balance oxygen
$$2H_2 + O_2 → 2H_2O$$

Step 3: Check balance
Left: H=4, O=2
Right: H=4, O=2 ✓

Final Answer: $2H_2 + O_2 → 2H_2O$
```

## Testing the System

### Test 1: Basic Math
**Ask:** "What is 1/2 + 1/4?"

**Expected:**
- Steps appear one by one (streaming)
- Fractions render as proper fractions
- Clear step markers
- Final answer formatted

### Test 2: Algebra
**Ask:** "Solve 3x - 7 = 14"

**Expected:**
- Each operation in separate step
- LaTeX formatting for equations
- Verification step included
- Understanding check at end

### Test 3: Coach Mode
**Switch to Coach mode, ask:** "How do I solve 2x + 5 = 15?"

**Expected:**
- Guiding questions first
- Hints with proper formatting
- Encourages student thinking
- Reveals solution gradually

### Test 4: Exam Mode
**Switch to Exam mode, ask:** "Solve x^2 - 4 = 0"

**Expected:**
- Direct, efficient solution
- All steps shown clearly
- Concise explanations
- Proper formatting maintained

## Configuration

The board-style teaching is configured in `ai_tutor/ai_utils.py`:

```python
def ask_ai(message, user=None, use_rag=True, learning_mode='explain'):
    # System prompt includes board-style instructions
    # Mode-specific formatting rules
    # LaTeX usage guidelines
```

No frontend changes needed - the AI naturally produces properly formatted responses that the frontend streaming and KaTeX rendering handle automatically.

## Benefits

### For Students:
✅ Clear, visual learning experience
✅ Easy to follow step-by-step
✅ Professional math formatting
✅ Feels like a real classroom
✅ Builds understanding gradually

### For Teachers:
✅ Consistent teaching structure
✅ Proper mathematical notation
✅ Adaptable to different learning modes
✅ Encourages best practices
✅ Scalable to any subject

## Summary

Nexa now teaches like a real classroom teacher:
- ✅ Board-style step-by-step solutions
- ✅ Professional LaTeX math formatting
- ✅ Streamed presentation (one step at a time)
- ✅ Visual teaching elements
- ✅ Adaptive to learning modes
- ✅ Understanding checks and engagement

Students experience authentic classroom teaching with the convenience of AI! 🎓
