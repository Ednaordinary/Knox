# Knox

<img width="300" height="300" alt="knox-round" src="https://github.com/user-attachments/assets/7369e379-34ee-4cd4-9259-a8186f80ae14" />


This is a bot for automatically printing [print legion](https://printlegion.hackclub.com/) 3D models.

It's made for the following setup:

- A1 printer printing PLA with an AMS
- Same network to the server (Linux)
- USPS Ground Advantage within the US for price calculation
- OrcaSlicer

Within slack it can

- [x] Download STL and STEP files from slack on command (converting STEP files to STL automatically)
- [x] Slice them
- [x] Estimate grams/ounces from a sliced file
- [x] Calculate shipping prices using that weight estimation
- [ ] Print the file on the printer once approved
- [x] Automatically remove prints from the bed

> [!NOTE]
> Most of the code in this repository was made to work well on the user end but not necessarily be easily maintainable. It is a product of the times. (I am aware the code's bad lol)
