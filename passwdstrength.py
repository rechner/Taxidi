#!/usr/bin/env python
#*-* coding:utf8 *-*

"""
Class for prompting for username/password, encrypting and storing passwords,
and checking password strength.
"""

import re

class StrengthChecker:
    def __init__(self, pwd_dict='', minLength=6):
        self.strengths = ['blank', 'very weak', 'weak', 'medium', 'strong', 'very strong', 'best']
        self.recommend = ['Password is blank!',
                          'at least %i characters' % minLength,
                          'one or more number',
                          'one capital and lowercase letter',
                          'one or more symbol']
        self.minLength = minLength

    def report(self, level, reqsMet=[]):
        if level < 0: level = 0
        if level > len(self.strengths): level = len(self.strengths)
        suggest = list(set(self.recommend) - set(reqsMet))
        if level == 0: suggest = self.recommend
        return (float(level)/(len(self.strengths)-1),
                self.strengths[level],
                suggest)

    def test(self, password):
        """
        Test a password for strength.  Returns tuple with strength between
        0 and 1.0, rating as string, and list of suggestions for a stronger
        password (For a stronger password, be sure to use...)

        Scores are one of the following:
        'blank', 'very weak', 'weak', 'medium', 'strong', 'very strong', 'best'
        """

        #test length
        score = 1
        met = [] #list of requirements the password met
        if len(password) < 1: return self.report(0)
        met.append(self.recommend[0]);
        if len(password) < 4: return self.report(1, met)
        if len(password) >= self.minLength: score += 1; met.append(self.recommend[1])
        if len(password) >= self.minLength+4: score += 1

        #reward for content over minLength
        if len(password) >= self.minLength:
            if re.search('\d+', password):  #one or more digit
                score += 1
                met.append(self.recommend[2])
            if re.search('[a-z]',password) and re.search('[A-Z]',password):
                score += 1
                met.append(self.recommend[3])
            if re.search('.[!,@,#,$,%,^,&,*,?,_,~,-,£,(,),<,>,\[,\],{,},\-]',password):
                score += 1
                met.append(self.recommend[4])

        return self.report(score, met)

if __name__ == '__main__':
    a = StrengthChecker()
    print a.test(raw_input("Enter a password to check > "))
