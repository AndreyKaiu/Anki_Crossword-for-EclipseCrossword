# Anki_Crossword-for-EclipseCrossword
Add-on for the Anki program. Creating a crossword for Anki (generation so far only with the free program [EclipseCrossword](https://www.eclipsecrossword.com/) ).

![Crossword1_0_1](https://github.com/user-attachments/assets/c03b464b-898f-474e-8103-b0ae88943b60)

![Crossword1_0_2](https://github.com/user-attachments/assets/94c2a84b-8882-4e58-a818-e5b79567b901)

![Crossword1_0_3](https://github.com/user-attachments/assets/5ebeb497-197a-48a1-9b1d-9d4d6d2fd132)

You will find the test deck (.apkg file) in the folder with the add-on or via the link [https://ankiweb.net/shared/info/1204327392](https://ankiweb.net/shared/info/1204327392)

![Crossword1_0_4](https://github.com/user-attachments/assets/3cf08bda-a285-4417-b776-85bf31c05f58)

![Crossword1_0_5](https://github.com/user-attachments/assets/a764e856-8671-449a-a807-7b569e894fc3)

![Crossword1_0_6](https://github.com/user-attachments/assets/c81e4105-b66f-4d1c-a048-d3d2f1dc0901)

![Crossword1_0_7](https://github.com/user-attachments/assets/f9ebac61-a441-4cf3-a813-6be2a6406dfd)


**CONTENTS OF THE HELP TAB**

This Anki add-on serves to simplify the creation of crosswords built using the free program https://www.eclipsecrossword.com/
The EclipseCrossword program is Windows-only, but you'll only need it once to generate the crossword code.

If you already have an EclipseCrossword saved as HTML with JavaScript, you can immediately open the last tab and use the 'Insert from file' button to get the crossword code.
In the ready crossword code, check that 'Word = new Array();' is empty, meaning the words aren't saved and there will be no hints.
And at the end of the code there's 'OnlyCheckOnce = false;' - this means you can check the crossword words multiple times, not just once.

The crossword itself appears on the back of the card. The front of the card can show words.
The words tab can be empty if you don't want any hints, or it can contain a simple word list (or clues).

In the words tab, you can enter not just words but word==translation (hint, definition).
By writing == you skip the transcription, which isn't needed in a regular crossword.
You can click the button to create data for the third tab or enter it manually, as the format isn't complicated:
word:  hint
(note there should be two spaces after the colon).

The word list data can be saved in '*.ewl' format and opened with EclipseCrossword to generate a new crossword, save it as '*.html' file, and then insert the crossword code from this file (button on the last tab).

Note that in the record besides the title there are two more fields: 'Language_SpeechSynthesis' and 'Symbols_for_buttons'.
Usually these fields are empty, then English is assumed and all button symbols are used. If your words are in another language, you need to enter a 'BCP 47 language tag' in the 'Language_SpeechSynthesis' field, for example 'de-DE' for German (without quotes of course).
The 'Symbols_for_buttons' field could be left empty, but if you use AnkiDroid, there's only button input to avoid using keyboard hints. On Android it's not very convenient to view large crosswords, and it's hard to memorize many words at once, so limit your crossword to about 20 words.

If you have foreign language word cards with fields: word, transcription, translation, example and example translation (field order doesn't matter). You can select these records in Anki and export them to a (.txt) file. Export as plain text without any other parameters. In the words tab there's a button to add words from a text file. If the field order is different, you'll need to modify the text field (1=2=3=4=5) before adding.

When a word has an example, you can create a word list with examples (there's a separate button for this), but since the example shouldn't hint the word, this word is replaced with ***. When you voice the word in the crossword, the example will also be voiced after it, as it's in the same language as the word.


**HELP AND SUPPORT**

**Please do not use reviews for bug reports or support requests.**<br>
**And be sure to like,** as your support is always needed. Thank you.
I don't get notified of your reviews, and properly troubleshooting an issue through them is nearly impossible. Instead, please either use the [issue tracker (preferred),](https://github.com/AndreyKaiu/Anki_Crossword-for-EclipseCrossword/issues) add-on [support forums](https://forums.ankiweb.net/t/add-ons-simple-image-occlusion-official-support/60307), or just message me at [andreykaiu@gmail.com.](mailto:andreykaiu@gmail.com) Constructive feedback and suggestions are always welcome!

**VERSIONS**
- 1.0, date: 2025-07-01. First release

**SPECIAL THANKS**
- Thanks to https://www.greeneclipse.com/ for the crossword generator program, for the source code of html and JavaScript of the crossword which was converted to work in Anki.
- Thanks for help in development: deepseek, chatgpt. But without them I definitely wouldn't have managed, since I don't program in Python and certainly not an Anki developer.
