Project Overview

This project provides the code required for the minitask2 unfolding process. Below is an introduction to the various files included in the repository.

Graph Files:

Original Graph Files: Graph files without any additional annotations in their filenames represent the raw input that is to be unfolded.

Unfolded Graph Files: Files with the suffix _unfold3 indicate that the original graph has been processed (i.e., unfolded) by our code using an unfolding factor of 3.

Unfolded Graph Files with Node Explanations: If the filename includes the suffix _unfold3_with_nodename, it means that, during the unfolding process, additional node explanations have been appended. For example, a node definition such as n4_2 [label="773:IFLE"]; will also include an extra line like 2:773:IFLE to provide further details.

Code Versions:

unfolding_final_1.py: This version incorporates most of the core functionalities but does not add the extra node explanations (for example, the 2:773:IFLE).

unfolding_final_nodename.py: This version outputs the unfolded graph along with the additional node name explanations.

PDF report:
minitask2_unfolding-report_mingshen_zhang.pdf
Uploaded 8/4/2025
