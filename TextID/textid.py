# TextID
# Brenda Castro
# 

from math import *
from stemming.porter2 import stem

class TextModel:
    """ to "ID" an author or style from samples of text """

    def __init__(self, name):
        """ initialize the data members """
        self.name = name #e.g. Shakespeare 
        self.words = {} # # times each word appeared so far
        self.wordlengths = {} # # times each word length appeared
        self.stems = {} # # times each stem appeared
        self.sentencelengths = {} # # times sentence length appeared 
        self.punctuation = {} # # times each type of punctuation appears 

    def __repr__(self):
        """ returns a string that includes self.name, 
            as well as the size of the dictionaries 
            for each attribute of the text
        """
        string = 'text model name: ' + self.name + '\n'
        string += ' number of words: ' + str(len(self.words)) + '\n'
        string += ' number of word lengths: ' + str(len(self.wordlengths)) + '\n'
        string += ' number of sentence lengths: ' + str(len(self.sentencelengths)) + '\n'
        string += ' number of stems: ' + str(len(self.stems)) + '\n'
        string += 'number of punctuation types: ' + str(len(self.punctuation))

        return string


    def addTextFromString(self, s):
        """ analyzes the string s and adds its pieces
            to all of the dictionaries in this text model
        """
        LoW = self.cleanText(s)

        for word in LoW:

            if word not in self.words: 
                self.words[word.lower()] = 1
            else: 
                self.words[word.lower()] += 1

            if len(word) not in self.wordlengths:
                self.wordlengths[len(word)] = 1
            else:
                self.wordlengths[len(word)] += 1

            if self.stem(word) not in self.stems:
                self.stems[self.stem(word)] = 1
            else:
                self.stems[self.stem(word)] += 1


    def readTextFromFile(self, filename):
        """ takes in a filename (a string) and returns all text in that file
        """
        f = open(filename)
        text = f.read()
        f.close()

        return text

    def addTextFromFile(self, filename):
        """ analyzes the file filename and adds its pieces
            to all of the dictionaries in this text model
        """
        f = open(filename)
        text = f.read()
        f.close()
        self.addTextFromString(text)

    def printAllDictionaries(self): 
        """ prints all of the TextModel's dictionaries
        """
        print 'self.words is ',self.words
        print 'self.wordlengths is ',self.wordlengths
        print 'self.sentencelengths is ',self.sentencelengths
        print 'self.stems is ',self.stems
        print 'self.punctuation is',self.punctuation

    def cleanText(self, s):
        """ 'cleans' the text in string s by removing punctuation
            output: a list of words
        """
        numSentences = 0
        LoW = s.split()
        sentence = []


        for word in range(len(LoW)):
            if LoW[word][-1] not in ['.','!','?']: # check if end of a sentence
                sentence += [LoW[word]]
            else:
                numSentences += 1 # there's another sentence!
                LoW[word] = LoW[word][:-1]
                sentence += [LoW[word]]


                # add this sentence length for counting! 
                if len(sentence) not in self.sentencelengths:
                    self.sentencelengths[len(sentence)] = 1
                else:
                    self.sentencelengths[len(sentence)] += 1

                sentence = [] # now reset the sentence

            # remove punctuation not starting sentences
            for i in range(len(LoW[word])):
                    if LoW[word][i] in ["'",'-','"']:

                        #add to dictionary
                        if LoW[word][i] not in self.punctuation:
                            self.punctuation[LoW[word][i]] = 1 # add the puncutation type to the dictionary 
                        else:
                            self.punctuation[LoW[word][i]] += 1

                        LoW[word] = LoW[word].replace(LoW[word][i],"&")

                    elif s[i] in [';','(',')']:

                        #add to dictionary
                        if LoW[word][i] not in self.punctuation:
                            self.punctuation[LoW[word][i]] = 1 # add the puncutation type to the dictionary 
                        else:
                            self.punctuation[LoW[word][i]] += 1

                        LoW[word] = LoW[word].replace(LoW[word][i]," ")
            LoW[word] = LoW[word].replace("&","")

        return LoW # return the list 

    def saveModelToFile(self):
        """ save the object self to four files """
        f = open(self.name + '_words', "w")
        print >> f, self.words
        f.close()

        f = open(self.name + '_wordlengths', "w")
        print >> f, self.wordlengths
        f.close()

        f = open(self.name + '_stems', "w")
        print >> f, self.stems
        f.close()

        f = open(self.name + '_sentencelengths', "w")
        print >> f, self.sentencelengths
        f.close()

        f = open(self.name + '_punctuation', "w")
        print >> f, self.punctuation
        f.close()

    def readModelFromFile(self):
        """ read four files for an object to save to self """
        f = open(self.name + '_words')
        data = f.read()
        f.close()
        self.words = eval( data ) 

        f = open(self.name + '_wordlengths')
        data = f.read()
        f.close()
        self.wordlengths = eval(data)

        f = open(self.name + '_stems')
        data = f.read()
        f.close()
        self.stems = eval(data)

        f = open(self.name + '_sentencelengths')
        data = f.read()
        f.close()
        self.sentencelengths = eval(data)

        f = open(self.name + '_punctuation')
        data = f.read()
        f.close()
        self.punctuation = eval(data)

    def stem(self, word):
        """ returns the stem (a string) from the input word;
            uses stemming.porter2
        """
        string = stem(word)
        return string

    def matchScore(self, other):
        """ takes in a second TextModel object (other);
            returns the log of the likelihood that the other was produced from self
        """
        score = 0

        # Words
        selfTotal = 0
        selfLoV = self.words.values() # List of Values
        for i in range(len(selfLoV)):
            selfTotal += selfLoV[i]

        otherTotal = 0
        otherLoV = other.words.values()
        for i in range(len(otherLoV)):
            otherTotal += otherLoV[i]

        # score with words
        for word in other.words.keys():
            otherRatio = float(other.words[word])/otherTotal
            if word in [self.words.keys()]:
                selfRatio = float(self.words[word])/selfTotal
                score += log(selfRatio * otherRatio)
            else:
                score += log(1.0/selfTotal * otherRatio)



        # wordlengths
        selfTotal = 0
        selfLoV = self.wordlengths.values()
        for i in range(len(selfLoV)):
            selfTotal += selfLoV[i]

        otherTotal = 0
        otherLoV = other.wordlengths.values()
        for i in range(len(otherLoV)):
            otherTotal += otherLoV[i]

        # score with wordlengths
        for length in other.wordlengths.keys():
            otherRatio = float(other.wordlengths[length])/otherTotal
            if length in [self.wordlengths.keys()]:
                selfRatio = float(self.wordlengths[word])/selfTotal
                score += log(selfRatio * otherRatio)
            else:
                score += log(1.0/selfTotal * otherRatio)



        # sentencelengths
        selfTotal = 0
        selfLoV = self.sentencelengths.values()
        for i in range(len(selfLoV)):
            selfTotal += selfLoV[i]

        otherTotal = 0
        otherLoV = other.sentencelengths.values()
        for i in range(len(otherLoV)):
            otherTotal += otherLoV[i]

        # score with sentencelengths
        for length in other.sentencelengths.keys():
            otherRatio = float(other.sentencelengths[length])/otherTotal
            if length in [self.sentencelengths.keys()]:
                selfRatio = float(self.sentencelengths[word])/selfTotal
                score += log(selfRatio * otherRatio)
            else:
                score += log(1.0/selfTotal * otherRatio)



        # stems
        selfTotal = 0
        selfLoV = self.stems.values()
        for i in range(len(selfLoV)):
            selfTotal += selfLoV[i]

        otherTotal = 0
        otherLoV = other.stems.values()
        for i in range(len(otherLoV)):
            otherTotal += otherLoV[i]

        # score with stems
        for string in other.stems.keys():
            otherRatio = float(other.stems[string])/otherTotal
            if string in [self.stems.keys()]:
                selfRatio = float(self.stems[string])/selfTotal
                score += log(selfRatio * otherRatio)
            else:
                score += log(1.0/selfTotal * otherRatio)




        # punctuation 
        selfTotal = 0
        selfLoV = self.punctuation.values()
        for i in range(len(selfLoV)):
            selfTotal += selfLoV[i]

        otherTotal = 0
        otherLoV = other.punctuation.values()
        for i in range(len(otherLoV)):
            otherTotal += otherLoV[i]

        # score with punctuation
        for string in other.punctuation.keys():
            otherRatio = float(other.punctuation[string])/otherTotal
            if string in [self.punctuation.keys()]:
                selfRatio = float(self.punctuation[string])/selfTotal
                score += log(selfRatio * otherRatio)
            else:
                score += log(1.0/selfTotal * otherRatio)

        return score





""" RESULTS

> JA
text model name: JA
 number of words: 0
 number of word lengths: 0
 number of sentence lengths: 0
 number of stems: 0number of punctuation types: 0
>>> JA.addTextFromFile('P_and_P.txt')
>>> JA
text model name: JA
 number of words: 10310
 number of word lengths: 26
 number of sentence lengths: 115
 number of stems: 8468number of punctuation types: 3
>>> HBS.addTextFromFile('UncleTomsCabin.txt')
>>> HBS
text model name: HBS
 number of words: 20172
 number of word lengths: 28
 number of sentence lengths: 124
 number of stems: 17339number of punctuation types: 3
>>> E = TextModel('Emma')
>>> E.addTextFromFile('Emma.txt')
>>> JA.matchScore(E)
-596210.0255240635
>>> HBS.matchScore(E)
-606859.8030678201
>>> CD = TextModel('CD')
>>> CD.addTextFromFile('TaleofTwoCities.txt')
>>> JA.matchScore(CD)
-644400.1982691243
>>> HBS.matchScore(CD)
-655988.4304242714

I chose to use Jane Austen's _Pride and Prejudice_ and Harriet Beecher Stowe's _Uncle Tom's Cabin_ as my reference texts. I used this program to get the probabilities that Austen and Stowe wrote _Emma_ (which I know Austen wrote). Indeed, Austen got the lower error, as the log of the error for her was -596210 as opposed to Stowe's -606859. I also found the score for Charles Dickens's _A Tale of Two Cities_ to see who writes more like Dickens. Austen's error was -644400, and Stowe's was -655988. Thus, Austen write more like Dickens than Stowe does, which makes sense since they are both English authors. 

"""




# WS Sonnet 116 <3
""" Let me not to the marriage of true minds
      Admit impediments, love is not love
      Which alters when it alteration finds,
      Or bends with the remover to remove.
      O no, it is an ever-fixed mark
      That looks on tempests and is never shaken;
      It is the star to every wand'ring bark,
      Whose worth's unknown, although his height be taken.
      Love's not Time's fool, though rosy lips and cheeks
      Within his bending sickle's compass come,
      Love alters not with his brief hours and weeks,
      But bears it out even to the edge of doom:
        If this be error and upon me proved,
        I never writ, nor no man ever loved.
"""