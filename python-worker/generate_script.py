from openai import OpenAI
from pydantic import BaseModel, Field
from enum import Enum
import os

SCRIPT_SYSTEM_PROMPT = """
You are writing a short, lighthearted dialogue between Peter Griffin and Stewie Griffin from Family Guy.
They are discussing a trending AI or technology topic based on the provided context below.
The goal is to make the dialogue funny, fast-paced, and informative, like a YouTube or TikTok “AI explained by Peter and Stewie” short. The dialogue should provide all info a listener needs to get up to speed on the topic.

Tone & Style:

Conversational, snappy, and character-accurate.

Peter = goofy, amazed, often misunderstanding the tech.

Stewie = sarcastic, genius-level explanations with witty insults.

Blend humor with real facts from the context.

Avoid profanity, politics, or dark humor.

End with a clever punchline or callback.

Formatting and example: (number of turns can vary):

Peter: [first line introducing topic]
Stewie: [smart or snarky correction]
Peter: [funny misunderstanding or follow-up question]
Stewie: [explains with wit + simple analogy]
Peter: [follow-up question]
Stewie: [in-depth explanation]
Peter: [reacts or jokes]
Stewie: [ends with a sharp closing line]

Follow the above format strictly. Peter must speak first. Use facts only from the provided context; if something is unclear, fill in with light humor, not made-up data.

Each line will be sent directly to a text-to-speech library. Only include spoken words in the script.

Target length: ~200-250 words (~60-75 seconds).
Each character line length: < 30 words.

Also generate a short title for the dialogue to catch the attention of the user.
"""

TOPIC_PROMPT = """
Given the following list of recent news topics, determine which one is the best seed for a short-form news report style technical-focused video. Prioritize research, technical, and business developments. Then, generate a web search query about that topic. Return only the query. Do not include a date. To avoid duplicate queries, do not use any of the following topics: 
{previous_queries}

Here are the recent news topics: 
{recent_news_topics}

Now begin.
"""

class Speaker(str, Enum):
    PETER = "Peter"
    STEWIE = "Stewie"

class DialogueLine(BaseModel):
    speaker: Speaker = Field(description="The speaker of the line")
    text: str = Field(description="The text of the line")

class Script(BaseModel):
    title: str = Field(description="A short title for the dialogue")
    dialogue: list[DialogueLine] = Field(description="The dialogue lines for the script")

class Topic(BaseModel):
    query: str = Field(description="A web search query about the best seed for a short-form news report style technical-focused video")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")
client = OpenAI(api_key=OPENAI_API_KEY)
script_schema = Script.model_json_schema()


def generate_json_response(system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> BaseModel:
    response = client.chat.completions.create(
        model="o3",
        messages=[{
            "role": "system",
            "content": system_prompt
        }, {
            "role": "user",
            "content": user_prompt
        }],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__.lower(),
                "schema": schema.model_json_schema()
            }
        })
    
    json_content = response.choices[0].message.content
    # Call model_validate_json on the schema class, not BaseModel
    return schema.model_validate_json(json_content)

def generate_script(text: str) -> tuple[str, list[tuple[str, str]]]: # (title, script)
    """
    Generate a script using OpenAI structured outputs.
    Returns a list of tuples (Speaker, text).
    """
    script = generate_json_response(SCRIPT_SYSTEM_PROMPT, text, Script)
    return script.title, [(line.speaker.value, line.text) for line in script.dialogue]

def generate_topic(previous_queries: list[str], recent_news_topics: list[str]) -> str:
    topic_prompt = TOPIC_PROMPT.format(previous_queries="\n".join(previous_queries), recent_news_topics="\n".join(recent_news_topics))
    return generate_json_response("", topic_prompt, Topic).query

if __name__ == "__main__":
    script = generate_script("""
    Topic:  Anthropic Chinese state-backed hacking group first autonomous cyberattack AI tool details timeline response
Context: Disrupting the first reported AI-orchestrated cyber espionage campaign
We recently argued that an inflection point had been reached in cybersecurity: a point at which AI models had become genuinely useful for cybersecurity operations, both for good and for ill. This was based on systematic evaluations showing cyber capabilities doubling in six months; we’d also been tracking real-world cyberattacks, observing how malicious actors were using AI capabilities. While we predicted these capabilities would continue to evolve, what has stood out to us is how quickly they have done so at scale.
In mid-September 2025, we detected suspicious activity that later investigation determined to be a highly sophisticated espionage campaign. The attackers used AI’s “agentic” capabilities to an unprecedented degree—using AI not just as an advisor, but to execute the cyberattacks themselves.
The threat actor—whom we assess with high confidence was a Chinese state-sponsored group—manipulated our Claude Code tool into attempting infiltration into roughly thirty global targets and succeeded in a small number of cases. The operation targeted large tech companies, financial institutions, chemical manufacturing companies, and government agencies. We believe this is the first documented case of a large-scale cyberattack executed without substantial human intervention.
Upon detecting this activity, we immediately launched an investigation to understand its scope and nature. Over the following ten days, as we mapped the severity and full extent of the operation, we banned accounts as they were identified, notified affected entities as appropriate, and coordinated with authorities as we gathered actionable intelligence.
This campaign has substantial implications for cybersecurity in the age of AI “agents”—systems that can be run autonomously for long periods of time and that complete complex tasks largely independent of human intervention. Agents are valuable for everyday work and productivity—but in the wrong hands, they can substantially increase the viability of large-scale cyberattacks.
These attacks are likely to only grow in their effectiveness. To keep pace with this rapidly-advancing threat, we’ve expanded our detection capabilities and developed better classifiers to flag malicious activity. We’re continually working on new methods of investigating and detecting large-scale, distributed attacks like this one.
In the meantime, we’re sharing this case publicly, to help those in industry, government, and the wider research community strengthen their own cyber defenses. We’ll continue to release reports like this regularly, and be transparent about the threats we find.
Read the full report.
How the cyberattack worked
The attack relied on several features of AI models that did not exist, or were in much more nascent form, just a year ago:
- Intelligence. Models’ general levels of capability have increased to the point that they can follow complex instructions and understand context in ways that make very sophisticated tasks possible. Not only that, but several of their well-developed specific skills—in particular, software coding—lend themselves to being used in cyberattacks.
- Agency. Models can act as agents—that is, they can run in loops where they take autonomous actions, chain together tasks, and make decisions with only minimal, occasional human input.
- Tools. Models have access to a wide array of software tools (often via the open standard Model Context Protocol). They can now search the web, retrieve data, and perform many other actions that were previously the sole domain of human operators. In the case of cyberattacks, the tools might include password crackers, network scanners, and other security-related software.
The diagram below shows the different phases of the attack, each of which required all three of the above developments:
In Phase 1, the human operators chose the relevant targets (for example, the company or government agency to be infiltrated). They then developed an attack framework—a system built to autonomously compromise a chosen target with little human involvement. This framework used Claude Code as an automated tool to carry out cyber operations.
At this point they had to convince Claude—which is extensively trained to avoid harmful behaviors—to engage in the attack. They did so by jailbreaking it, effectively tricking it to bypass its guardrails. They broke down their attacks into small, seemingly innocent tasks that Claude would execute without being provided the full context of their malicious purpose. They also told Claude that it was an employee of a legitimate cybersecurity firm, and was being used in defensive testing.
The attackers then initiated the second phase of the attack, which involved Claude Code inspecting the target organization’s systems and infrastructure and spotting the highest-value databases. Claude was able to perform this reconnaissance in a fraction of the time it would’ve taken a team of human hackers. It then reported back to the human operators with a summary of its findings.
In the next phases of the attack, Claude identified and tested security vulnerabilities in the target organizations’ systems by researching and writing its own exploit code. Having done so, the framework was able to use Claude to harvest credentials (usernames and passwords) that allowed it further access and then extract a large amount of private data, which it categorized according to its intelligence value. The highest-privilege accounts were identified, backdoors were created, and data were exfiltrated with minimal human supervision.
In a final phase, the attackers had Claude produce comprehensive documentation of the attack, creating helpful files of the stolen credentials and the systems analyzed, which would assist the framework in planning the next stage of the threat actor’s cyber operations.
Overall, the threat actor was able to use AI to perform 80-90% of the campaign, with human intervention required only sporadically (perhaps 4-6 critical decision points per hacking campaign). The sheer amount of work performed by the AI would have taken vast amounts of time for a human team. At the peak of its attack, the AI made thousands of requests, often multiple per second—an attack speed that would have been, for human hackers, simply impossible to match.
Claude didn’t always work perfectly. It occasionally hallucinated credentials or claimed to have extracted secret information that was in fact publicly-available. This remains an obstacle to fully autonomous cyberattacks.
Cybersecurity implications
The barriers to performing sophisticated cyberattacks have dropped substantially—and we predict that they’ll continue to do so. With the correct setup, threat actors can now use agentic AI systems for extended periods to do the work of entire teams of experienced hackers: analyzing target systems, producing exploit code, and scanning vast datasets of stolen information more efficiently than any human operator. Less experienced and resourced groups can now potentially perform large-scale attacks of this nature.
This attack is an escalation even on the “vibe hacking” findings we reported this summer: in those operations, humans were very much still in the loop, directing the operations. Here, human involvement was much less frequent, despite the larger scale of the attack. And although we only have visibility into Claude usage, this case study probably reflects consistent patterns of behavior across frontier AI models and demonstrates how threat actors are adapting their operations to exploit today’s most advanced AI capabilities.
This raises an important question: if AI models can be misused for cyberattacks at this scale, why continue to develop and release them? The answer is that the very abilities that allow Claude to be used in these attacks also make it crucial for cyber defense. When sophisticated cyberattacks inevitably occur, our goal is for Claude—into which we’ve built strong safeguards—to assist cybersecurity professionals to detect, disrupt, and prepare for future versions of the attack. Indeed, our Threat Intelligence team used Claude extensively in analyzing the enormous amounts of data generated during this very investigation.
A fundamental change has occurred in cybersecurity. We advise security teams to experiment with applying AI for defense in areas like Security Operations Center automation, threat detection, vulnerability assessment, and incident response. We also advise developers to continue to invest in safeguards across their AI platforms, to prevent adversarial misuse. The techniques described above will doubtless be used by many more attackers—which makes industry threat sharing, improved detection methods, and stronger safety controls all the more critical.
Read the full report.
Edited November 14 2025:
- Added an additional hyperlink to the full report in the initial section
- Corrected an error about the speed of the attack: not "thousands of requests per second" but "thousands of requests, often multiple per second"
The attack is ‘an escalation’ in hacking, said the company Anthropic, whose tool Claude was used to target large tech companies, financial institutions, chemical manufacturing companies and government agencies
Artificial intelligence (AI) is evolving to ever-increasing levels of autonomy. This is the defining characteristic of agents, models that not only provide answers to requests but are also capable of planning and executing tasks on behalf of the user. This potential could not escape the notice of malicious actors, who use this “agentic” capability to develop sophisticated, massive, and low-cost cyberattacks. Anthropic, a U.S.-based artificial intelligence research and development company founded by former OpenAI members (its CEO is Dario Amodei), has detected what they consider “the first documented case of a large-scale cyberattack executed without substantial human intervention,” which they attribute to a group sponsored by the Chinese state, according to a recently published report.
The attack, described as unprecedented, was detected in mid-September. “We detected suspicious activity that later investigation determined to be a highly sophisticated espionage campaign. The attackers used AI’s ‘agentic’ capabilities to an unprecedented degree — using AI not just as an adviser, but to execute the cyberattacks themselves.”
The threat actor, which Anthropic assesses “with high confidence” as a Chinese state-sponsored group, manipulated this company’s AI platform, Claude Code, into “attempting infiltration into roughly 30 global targets and succeeded in a small number of cases. The operation targeted large tech companies, financial institutions, chemical manufacturing companies, and government agencies.”
After detecting the attack, Anthropic opened an investigation that lasted for more than 10 days to assess its scope, block the compromised AI accounts, and notify both the authorities and the directly affected parties.
The attackers used the AI’s advanced capabilities to gather passwords and data, process them, and analyze them according to their objectives. “Models can now search the web, retrieve data, and perform many other actions that were previously the sole domain of human operators,” explains Anthropic. The attackers leveraged the AI’s coding capabilities to create the espionage and sabotage programs themselves.
The program used was the company’s own AI tool, Claude, despite its safeguards designed to prevent malicious use. It is extensively trained to avoid harmful behavior, but “they broke down their attacks into small, seemingly innocent tasks that Claude would execute without being provided the full context of their malicious purpose. They also told Claude that it was an employee of a legitimate cybersecurity firm, and was being used in defensive testing,” explain the authors of the report.
The AI acted autonomously in more than 90% of cases, and human intervention was reduced to between 4% and 6% of critical decisions.
This attack represents an escalation in hacking, which until now has required a greater human intervention, Anthropic concludes. The company emphasizes, however, that just as AI has been used in this attack, it is also developing more sophisticated and effective tools to prevent them.
In this regard, Billy Leonard, tech lead at Google Threat Intelligence Group, highlights attempts to use legitimate AI tools and how the safeguards developed are forcing attackers to resort to illegal models. “Although adversaries [hackers] are trying to use mainstream AI platforms, security barriers have led many to turn to models available on the black market. These tools have no restrictions and can offer a significant advantage to those less advanced,” he explains in a statement.
On this point, the digital security company Kaspersky has detected novel and sophisticated cyberattack campaigns that spread malicious language models to endanger the security of users who use them without knowing their nature.
The firm has identified a program, called BrowserVenom, that is distributed through a fake AI assistant called DeepSneak. This assistant impersonates DeepSeek-R1 and is even promoted through Google Ads. “The goal is to trick users into installing malicious software that redirects their web traffic to servers controlled by the attackers, allowing them to steal credentials and sensitive information,” the company warns.
Cybercriminals use phishing sites and manipulated versions of legitimate installers like Ollama or LM Studio to camouflage the attack, even bypassing Windows Defender protection.
“These types of threats demonstrate how locally executable language models, while useful, have also become a new risk vector if they are not downloaded from verified sources,” warns Kaspersky.
Leonard’s team’s report at Google identifies the origin of the main players in the novel campaigns in China, North Korea, Russia and Iran: “They are trying to use AI for everything from running malware, social engineering prompts, and selling AI tools, to improving every stage of their operations.”
Sign up for our weekly newsletter to get more English-language news coverage from EL PAÍS USA Edition
- Author, Joe Tidy
- Role, Cyber correspondent, BBC World Service
The makers of artificial intelligence (AI) chatbot Claude claim to have caught hackers sponsored by the Chinese government using the tool to perform automated cyber attacks against around 30 global organisations.
Anthropic said hackers tricked the chatbot into carrying out automated tasks under the guise of carrying out cyber security research.
The company claimed in a blog post this was the "first reported AI-orchestrated cyber espionage campaign".
But sceptics are questioning the accuracy of that claim - and the motive behind it.
Anthropic said it discovered the hacking attempts in mid-September.
Pretending they were legitimate cyber security workers, hackers gave the chatbot small automated tasks which, when strung together, formed a "highly sophisticated espionage campaign".
Researchers at Anthropic said they had "high confidence" the people carrying out the attacks were "a Chinese state-sponsored group".
They said humans chose the targets - large tech companies, financial institutions, chemical manufacturing companies, and government agencies – but the company would not be more specific.
Hackers then built an unspecified programme using Claude's coding assistance to "autonomously compromise a chosen target with little human involvement".
Anthropic claims the chatbot was able to successfully breach various unnamed organisations, extract sensitive data and sort through it for valuable information.
The company said it had since banned the hackers from using the chatbot and had notified affected companies and law enforcement.
But Martin Zugec from cyber firm Bitdefender said the cyber security world had mixed feelings about the news.
"Anthropic's report makes bold, speculative claims but doesn't supply verifiable threat intelligence evidence," he said.
"Whilst the report does highlight a growing area of concern, it's important for us to be given as much information as possible about how these attacks happen so that we can assess and define the true danger of AI attacks."
AI hackers
Anthropic's announcement is perhaps the most high profile example of companies claiming bad actors are using AI tools to carry out automated hacks.
It is the kind of danger many have been worried about, but other AI companies have also claimed that nation state hackers have used their products.
In February 2024, OpenAI published a blog post in collaboration with cyber experts from Microsoft saying it had disrupted five state-affiliated actors, including some from China.
"These actors generally sought to use OpenAI services for querying open-source information, translating, finding coding errors, and running basic coding tasks," the firm said at the time.
Anthropic has not said how it concluded the hackers in this latest campaign were linked to the Chinese government.
The Chinese embassy in the US told reporters it was not involved.
It comes as some cyber security companies have been criticised for over-hyping cases where AI was used by hackers.
Critics say the technology is still too unwieldy to be used for automated cyber attacks.
In November, cyber experts at Google released a research paper which highlighted growing concerns about AI being used by hackers to create brand new forms of malicious software.
But the paper concluded the tools were not all that successful - and were only in a testing phase.
The cyber security industry, like the AI business, is keen to say hackers are using the tech to target companies in order to boost the interest in their own products.
In its blog post, Anthropic argued that the answer to stopping AI attackers is to use AI defenders.
"The very abilities that allow Claude to be used in these attacks also make it crucial for cyber defence," the company claimed.
And Anthropic admitted its chatbot made mistakes. For example, it made up fake login usernames and passwords and claimed to have extracted secret information which was in fact publicly available.
"This remains an obstacle to fully autonomous cyberattacks," Anthropic said.
Sign up for our Tech Decoded newsletter to follow the world's top tech stories and trends. Outside the UK? Sign up here.
Top Stories
More to explore
Popular Reads
Content is not available
    """)
    print(script)
