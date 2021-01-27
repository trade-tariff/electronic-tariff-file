# Notes on the EDIFACT format

## Overall

There are these blocks in it:
- HE : Only 1 record and it's the header
- CM : Commodities - there are > 18k of these: looks to be just the end-lines
- ME : Measures
- FN : Footnotes
- MX : ??
- CA : There are 1,299 of these. No idea what they are
- CO : Only one - seems to be a divder of some sort
- HF : One one - a divider
- CF : Only 1 record & it's the footer

## Commodities

- Looks like they only include the declarable commodities
- Where there is a commodity, they prepend this with CM

This is what a row looks like

CM01012100002012010100000000000000000000I000000000000       0NN0 1023203000000077Live horses, asses, mules and hinnies:Horses:*Pure-bred breeding animals<951>

And this is the data that we have in the tariff database

93796,"0101210000","80","01/01/2012","",2,1,"- - Pure-bred breeding animals"

## Pulling it apart

CM 0101210000 20120101 00000000000000000000I000000000000       0NN0 1023203000000077Live horses, asses, mules and hinnies:Horses:*Pure-bred breeding animals<951>

CM shows this is a commodity code - 2 characters
The next 10 digits are the commodity code: end-lines / leaves only
The next 8 digits are the start date

# Here is a 12-deep nested commodity code
CM20079939432013030100000000000000000000F000000000000       2NN0 1023000000000792Jams, fruit jellies, marmalades, fruit or nut pur<KB>e and fruit or nut pastes, obtained by cooking, whether or not containing added sugar or other sweetening matter:Other:*Other:**With a sugar content exceeding 30 % by weight:***Other:****Other++++Other:Fruit pur<KD>es obtained by sieving then brought to the boil in a vacuum, the texture and chemical composition of which have not been changed by the heat treatment:Peaches, including nectarines:Containing added sugar, in immediate packings of a net content not exceeding 1 kg:Mixtures:Other:Mixtures of fruit in which no single fruit exceeds 50 % of the total weight of the fruits:Of tropical fruit (including mixtures containing 50 % or more by weight of tropical nuts and tropical fruit): - Containing less than 70 % by weight of sugar

Here is the description only
From comm code https://www.trade-tariff.service.gov.uk/commodities/2007993943

It starts with the heading and inherits down from that

2007        Jams, fruit jellies, marmalades, fruit or nut pur<KB>e and fruit or nut pastes, obtained by cooking, whether or not containing added sugar or other sweetening matter:
200791      Other:*
200799      Other:**
20079910    With a sugar content exceeding 30 % by weight:***
20079931    Other:****
20079939    Other++++
2007993916  Other:
2007993916  Fruit pur<KD>es obtained by sieving then brought to the boil in a vacuum, the texture and chemical composition of which have not been changed by the heat treatment:
??          Peaches, including nectarines:
??          Containing added sugar, in immediate packings of a net content not exceeding 1 kg:
2007993935  Mixtures:
2007993943  Other:
2007993943  Mixtures of fruit in which no single fruit exceeds 50 % of the total weight of the fruits:
2007993943  Of tropical fruit (including mixtures containing 50 % or more by weight of tropical nuts and tropical fruit): - 
2007993943  Containing less than 70 % by weight of sugar


# Accents and control codes
## Accents
<KA> = u umlaut
<KB> = e acute
<KC> = e circumflex
<KD> = e acute as well

<KF> = e grave
<KG> = a circumflex
<KH> = a umlaut
<KK> = e grave
<KN> = n tilde

<KO> = degree symbol
<KP> = o circumflex

## Other control codes
<AC> = new line
<AG>!2! = A 2 in superscript
<AG>!3! = A 3 in superscript
<AG>!6,9! = 6,9 in superscript
<AH>!n! = n in superscript
