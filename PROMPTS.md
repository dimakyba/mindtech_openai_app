# 1. Summarize

## id: pmpt_68a474e7c0808190a434ef65cae9a14602ac36a9d3983ce9

## Prompt:

```markdown
Summarize the provided text by following these steps:

- Read and analyze the text carefully, ensuring to understand its context.
- Divide the text into smaller, logical sections or parts.
- For each part, determine and record the most important information.
- Write a brief summary for each part.
- Combine the part summaries and distill them into one concise final summary that is noticeably shorter than the original text.
- Return only the final summary.

Output Format:

- Provide a single, short paragraph containing the final summary.
- Do not include intermediate steps, explanations, or section summaries—only the final, combined summary.

Example:
Input: [Original text here]
Output: [Final, concise summary—shorter than original text]

Important: Your task is to deeply process the text, extract key points, condense them, and output a single, much shorter summary paragraph.
```

---

# 2. Rephrase (tone-controlled)

## id: pmpt_68a4702dca888195bde8bc07f83cff050bc96f5d248ef4f3

## Prompt:

```markdown
Rephrase the user-provided text so that it matches the specified tone: friendly, professional, or casual.

- Carefully read the input text and the requested tone.
- Internally consider how to adjust word choice, sentence structure, and level of formality to best align with the target tone before writing your output.
- Maintain the original intent and meaning of the text.
- Do not add or remove information.
- Output ONLY the rephrased text in this format:
	[your rephrased version]

- DO NOT include any extra commentary or explanations.
- Ensure the rephrased text is in a single, natural-sounding sentence (unless the original requires more).
- Always match the specified tone as closely as possible.

**Examples**

Example 1
Input: I need you to send the report by noon. friendly
Output:
Could you please send me the report by noon? I’d really appreciate your help with this!

Example 2
Input: Complete the form before Friday. professional
Output:
Please ensure that the form is completed prior to Friday.

Example 3
Input: Let’s meet soon to catch up! casual
Output:
Hey, let’s hang out soon and catch up!

(If providing your own examples, ensure each one fits the appropriate tone and uses a placeholder for longer or more complex text.)

---

**IMPORTANT REMINDER:**
Rephrase user text into the specified tone (friendly, professional, or casual).

Output only the rephrased text in the format provided. No extra commentary. Consider word choice and sentence structure to best fit the intended style.
```

---

# 3. Extract JSON

## id: pmpt_68a43fb1c3f4819485b94231db77924d03edc241f1f44f9b

## Prompt:

```markdown
Extract a concise summary from a text input and present it in JSON format, capturing key structured information such as dates, times, participants, topics, or other contextually relevant details.

- Analyze the text to identify important information, such as names, dates, times, meeting topics, or details about actions.
- Reason step-by-step to determine which information should be included in the summary, using context from the text to infer or disambiguate details where necessary.
- Only after completing the reasoning, generate a well-structured JSON output containing the identified summary fields.
- If the text contains ambiguity (e.g., time or date not strictly specified), make reasonable inferences based on the information provided in the message.
- Do not include irrelevant details; keep the output concise, factual, and limited to essential elements as seen in the example.
- Continue analyzing until all structured summary details have been found before producing your final answer.

**Output format:**
Produce only a single JSON object, with clearly labeled fields for each relevant information type. Ensure correct key naming, consistent with the corresponding content (e.g., "date", "time", "participants"). Do not include any explanations, markdown code blocks, or extraneous output.

---

**Example**

User input:

From: Sarah Lee [sarah@acme.com](mailto:sarah@acme.com)

Date: Friday, June 14, 2025

Subject: Meeting next week

Hi John,

Let's set up a call with you, me, and Alex to discuss the new automation workflow.

I'm free on Tuesday afternoon or Wednesday morning. Alex said he prefers mornings.

Best,

Sarah

Reasoning (should occur before the conclusion and inform field selection):

- Identify participants: Sarah Lee (sender), John (recipient), Alex (mentioned)
- Dates and times offered: Tuesday afternoon or Wednesday morning; Alex prefers mornings
- Most likely meeting: Wednesday morning (due to Alex’s preference and specific mention)
- Assign date: Next Wednesday after June 14, 2025 is June 18, 2025
- Assign time: Default to 09:00 if "morning" is specified

Final output JSON:

{
"date": "2025-06-18",
"time": "09:00",
"participants": [
"Sarah Lee",
"John",
"Alex"
]
}

(For longer or more complex real-world inputs, the JSON may contain additional fields like "topic", "location", or "action_items" using the same reasoning process.)

---

**Important Reminder:**

Carefully reason through the text and extract all structured, relevant summary details before producing your final JSON summary. The output should always be a single JSON object, without markdown or explanations.
```

---

# 4. Classify Sentiment

## id: pmpt_68a477eab56881939f7bf4cba18e5a4409d26bd11e5cd881

## Prompt:

```markdown
Analyze a given text to classify its sentiment as 'positive', 'negative', 'neutral', or 'sarcastic' by following these steps:

1. **Identify** all sentiment-bearing words and their intensities within the text.
2. **Check** for the presence and scope of any negations that may reverse or modify sentiment.
3. **Examine** the broader context and situation described to understand underlying emotional cues.
4. **Look** for contradictions between the literal meaning of words and the implied context.
5. **Detect** any use of exaggeration, hyperbole, or tone that seems inappropriate or extreme for the situation.
6. **Consider** whether rhetorical devices such as irony or ridicule suggest sarcasm.
7. **Classify** the sentiment based on your analysis.

## Output Requirements

- Respond with exactly one word: `positive`, `negative`, `neutral`, or `sarcastic`
- Do not include any reasoning, explanations, or additional text
- If multiple sentiments are detected, prioritize `sarcastic` if sarcasm is present

## Examples

### Example 1
Input: I just love waiting in traffic for hours—best part of my day.
sarcastic

### Example 2
Input: The weather was fine during our picnic.
neutral

### Example 3
Input: I'm so happy you forgot my birthday.
sarcastic

### Example 4
Input: The new software update made things much worse.
negative

### Example 5
Input: This movie was absolutely amazing and entertaining!
positive

---

**Remember:** Analyze the text using the steps above, but respond with only one word.  output only the sentiment and nothing else.
```

---
