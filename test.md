Apparently, digital noise is a thing.



Over the last few weeks, I got incredibly frustrated trying to keep up with the endless stream of AI news, research papers, and technical blogs. And it always felt like I was "missing out" on some very crucial information. Maybe a new research paper, or a new model release, or something else. I didn't know where to search (if you do, please tell me about it). And so I spent a few hours everyday searching on google, X, wherever basically. This was not very useful and I am damn sure I was still missing out. So I decided to take things into my own hands. 



I wanted a system that understood my technical standing and filtered out the noise. So, I spent the last week developing PULSE: a self hosted AI recommendation engine and your personal autonomous researcher that wakes up, surfs the web and sends an email digest daily. 



Here's a high level overview of the components involved:



- An Autonomous Crawler: Safely navigates the web, extracts pure, high-signal technical text, and completely ignores ads and cookie banners.



- A Context-Aware Brain: Uses the Groq API to generate technical summaries. Crucially, it reads my specific user profile and tailors the depth of the summaries directly to my technical standing. 



- A Vector Gatekeeper: Uses FastEmbed to generate 384-dimensional vectors locally and securely locks them into Qdrant Cloud for semantic matching.



- The Feedback Loop: probably the most important and the most time consuming part of the project. technical understanding and interests change regularly. Orchestrated by FastAPI, the system sends me a daily digest with feedback buttons. Clicking these buttons hits webhooks that change the user profile on the fly, actively mitigating concept drift without me having to write another line of code.



What's Next? PULSE v0.1 is officially operational. It does require cloning the gituhb repo and setting up env variables. However, I am already building the next version which will include a user friendly UI, db integration, cleaner vector searches, and hopefully better overall performance.



I tested this myself and am pleased with the result. Not satisfied yet so I'll continue working on it. 



Link to GitHub repository: https://github.com/rshaurya/pulse



For the people who didn't open the github repo: if you're someone who could benefit from this but don't want to or are facing difficulty in setting it up, I'd suggest waiting for a week or two. The deployed, user friendly version would be out by then :) 



And if you're current domain or field of interest does not lie in tech, feel free to comment, DM or send an email with your domain / field of interest. This will help me test the app before it reaches you. 



I put a halt to my schedule of learning ml and built this :) Atleast I have something to read while sipping my morning coffee. 