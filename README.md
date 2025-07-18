# Knox

This is a bot for automatically printing [print legion](https://printlegion.hackclub.com/) 3D models.

It's made for the following setup:

- A1 printer printing PLA with an AMS
- Same network to the server (Linux)
- USPS Ground Advantage within the US for price calculation
- OrcaSlicer

Within slack it can

- [ ] Download STL and STEP files from slack on command (converting STEP files to STL automatically)
- [ ] Slice them
- [x] Estimate grams/ounces from a sliced file
- [ ] Use that weight estimation to
- [x] Calculate shipping prices
- [ ] Send the file to the printer once approved
