Evaluation Results

Evaluation of the RAG assistant over 12 Azure and AWS documentation PDFs (111 pages).

All numbers come from my own runs. The test set has 25 questions: 22 answerable and 3 unanswerable. The questions were written once and not changed to improve scores.

Setup
Embeddings: sentence-transformers/all-MiniLM-L6-v2 (local)
Vector database: Chroma
Answer model: gemini-3.5-flash-lite (free tier)
Chunk settings tested: 300 / 50, 800 / 100 and 1500 / 200 (chunk size / overlap, in characters)
1. Retrieval test (no Gemini calls)

Two measures, on the 22 answerable questions:

File hit: the expected PDF appears in the top-k chunks.
Keyword hit: every expected keyword appears in the text of the top-k chunks.
Chunk size	Overlap	    Chunks	Top-2 file	        Top-2 keyword	Top-4 file	    Top-4 keyword
300	           50	    819	        100%(22/22)	     68% (15/22)	100% (22/22)	86% (19/22)
800	           100	    519	        100%(22/22)	     77% (17/22)	100% (22/22)	82% (18/22)
1500	       200	    190	         95%(21/22)	     86% (19/22)	100% (22/22)	95% (21/22)

Notes:

File hit rate is high because the 12 documents cover different topics, so finding the right file is easy. Keyword hit is the measure that shows differences between settings.
Top-2 keyword hit rises with chunk size (15, 17, 19 questions).
The comparison is not equal in context size. Top-4 at 1500 sends up to about 6000 characters to the model, against about 3200 at 800 and about 1200 at 300. Part of the gain at 1500 may come from the larger context, not better search.
One question is worth about 4.5 percentage points, so small differences could be noise.
2. Answer accuracy (uses Gemini, top-4 chunks)

A question passes when the answer contains every expected keyword. An unanswerable question passes only when the answer is "I could not find this in the documents".

Chunk size	    Overlap	    Accuracy	    Average response time
800	            100	        19/25 = 76%	    1.4 s
1500	        200	        21/25 = 84%	    1.5 s

Result: 1500 / 200 scored 2 questions higher than the baseline. It also scored higher in the retrieval test, so two measures point the same way. With 25 questions this is a modest improvement, not a large one. Response time is the same for practical purposes.

Final setting chosen: chunk size 1500, overlap 200.

The 300 / 50 setting was tested for retrieval only, not for answer accuracy, because its retrieval scores did not beat the other two settings at both top-k values.

3. Failures at 1500 / 200
Q	Question	What happened	Cause
5	How can we get list of available locations?	Answer gave PowerShell, REST API and CLI methods but not the Azure portal.	Incomplete answer.
9	What is Blobfuse?	"I could not find this in the documents".	Retrieval miss. The right file was found but not the right chunk. The model refused instead of guessing.
11	How to filter network traffic between subnets?	Answered "Network security groups" and "Application security groups". Expected "Network virtual appliances" as well.	Likely answer error: retrieval had found the missing phrase. 
14	What is used to maximize resource utilization?	Answered "move existing single databases into a resource pool".	Correct in meaning, but it does not use the expected term "Elastic Pools", so the strict keyword check failed it.

Measured accuracy stays at 21/25 = 84%. My own manual reading counts Q14 as correct in meaning, which would give about 22/25 = 88%. This is a manual estimate, not the measured score.

At the 800 / 100 baseline, Q6, Q9, Q11, Q14, Q19 and Q23 failed. Q6, Q19 and Q23 pass at 1500 / 200. Q5 passes at 800 / 100 and fails at 1500 / 200. The baseline answers for Q6, Q19 and Q23 were not reviewed by hand.

4. Unanswerable questions

All 3 unanswerable questions (Q4, Q10, Q25) returned "I could not find this in the documents" in both settings. The assistant did not invent answers for them.

5. Limitations
The keyword check is strict. A correct answer in different words can fail, as in Q14.
The test set is small (25 questions), so one question moves the score by 4 points.
Saved web pages carry menu and header text, which becomes noise in some chunks.
When the answer is "not found", the assistant still lists source pages. It would be better to hide them.
Response time includes one slow first call (about 10 seconds for Q1). The other questions took 0.6 to 1.9 seconds.
The 6 second pause between questions in the test script is a guess for the free-tier rate limit.
6. Ingest numbers (1500 / 200)
Files: 12
Total pages: 111
Total chunks: 190
Ingest time: under a minute (15 to 43 seconds across runs; model loading varies)