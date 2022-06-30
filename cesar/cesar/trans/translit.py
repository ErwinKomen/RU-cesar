"""
Transliteration conversion between Latin (academic) script and Cyrillic (standard) script of Chechen

Erwin R. Komen - May 2021
"""
import re
import sys

# This conversion list is orderd long-to-short and contains four elements per unit:
# 1: full latin (lower case) to be recognized
# 2: syllabls (V=vowel, C=consonant, D=diphthong, C#=end-of-syllable consonant)
# 3: cyrillic translation
# 4: cyrillic translation in *open* syllable (usually left blank)
# 5: cyrillic translation: syllable-initial
# 6: cyrillic translation: syllable-initial in *open* syllable
lst_latin_c = [
    "bw_CC_бІ", "b_C_б",
    "cch'_CC_ччІ", "cCh'_CC_цчІ", "ch'_C_чІ", "chw_CC_чхь",
    "cchw_CCC_ччхь","cch_CC_чч", "cCh_CC_цч", "ch_C_ч", "c'_C_цІ", "cw_CC_цхь", "c_C_ц",
    "d'_C_д.", "dw_CC_дІ", "d_C_д",
    "f_C_ф",
    "ggh_CC_ггІ", "gh_C_гІ", "g_C_г", 
    "hhw_CC_ххь", "hw_C_хь", "hh_CC_ххІ", "h_C_хІ",
    "j_C_й",
    "kx_CC_кьх", "kk'_CC_ккІ", "k'_C_кІ", "k_C_к",
    "lhw_CC_лхь", "lh_CC_лхІ", "l_C_л",
    "mw_CC_мІ", "m_C_м",
    "nw_CC_нІ", "n_C_н",
    "p'_C_пІ", "pw_CC_пхь", "p_C_п",
    "qq'_CC_ккъ", "qq_CC_ккх", "q'_C_къ", "q_C_кх",
    "rhw_CC_рхь", "rrh_CC_ррхІ", "rhh_CCC_рххІ", "rh_C_рхІ", "r_C_р",
    "shw_CC_шхь", "ssh_CC_шш", "sh_C_ш", "sw_CC_схь", "s_C_с", 
    "tw_CC_тхь", "t'_C_тІ", "t_C_т",
    "v_C_в",
    "w_C_І",
    "xhw_CC_хъхь", "xw_CC_хъхь", "x_C_х",
    "zzh_CC_жж", "zhw_CC_жІ", "zw_CC_зхь", "zh_C_ж", "z_C_з",
    "''_CC_ъ", "'_C_",
    "-_C_-"
    ]
vowel_lat = "aeiouy"

lat_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Note the order: start / mid / after 'j'
lst_latin_vs = [
    "aa_VV_а_а_я",    "ae_V_аь_аь_яь",     "a_V_а_а_я", 
    "ee_VV_э_е_е",    "eE_VV_э̄_ē_ē",       "e_V_э_е_е", 
    "ie_D_иэ_иэ_йиэ", "ii_VV_ий_ий_йий",   "i_V_и_и_йи", 
    "oo_VV_о_о_йо",   "oe_D_оь_оь_йоь",    "o_V_о_о_йо",
    "uo_D_о_о_йо",    "uu_VV_у_у_ю",       "u_V_у_у_ю",
    "yy_VV_у_у_ю",    "ye_D_оь_оь_йоь",    "y_V_уь_уь_юь"
    ]
lst_latin_v = [
    "aa_VV_а_ā", "aj'ie_VCD_айе", "ae_V_аь", "a_V_а_а",
    "ee_VV_е_ē_э_э̄", "eE_VV_ē__э̄",
    "ie_D_е_е_э_э", "iijie_VVCD_ийе", "iiji_VVCV_ийи", "ii_VV_ий", "i_V_и",
    "jaa_CVV_я_я̄_ъя_ъя̄", "jae_CV_яь__ъяь",          "ja_CV_я__ъя", 
    "jee_CVV_е_ē_ъе_ъē", "je_CV_е__ъе",             "jie_CD_е_иэ_ъе_ъиэ",
    "juu_CVV_ю_ю̄_ъю_ъю̄", "juo_CD_йо_йō_ъйо_ъйуо",   "ju_CV_ю__ъю",
    "jyy_CVV_юьй__ъюьй", "jye_CD_йоь__ъйоь",        "jy_CV_юь__ъюь",
    "j_C_й",
    ]
lst_keep = [
    "doocch_CVVCC_доцч", "voocch_CVVCC_воцч", "joocch_CVVCC_йоцч", "boocch_CVVCC_боцч",
    ]

class ErrHandle:
    """Error handling"""

    # ======================= CLASS INITIALIZER ========================================
    def __init__(self):
        # Initialize a local error stack
        self.loc_errStack = []

    # ----------------------------------------------------------------------------------
    # Name :    Status
    # Goal :    Just give a status message
    # History:
    # 6/apr/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def Status(self, msg):
        """Put a status message on the standard error output"""

        print(msg, file=sys.stderr)

    # ----------------------------------------------------------------------------------
    # Name :    DoError
    # Goal :    Process an error
    # History:
    # 6/apr/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def DoError(self, msg, bExit = False):
        """Show an error message on stderr, preceded by the name of the function"""

        # Append the error message to the stack we have
        self.loc_errStack.append(msg)
        # get the message
        sErr = self.get_error_message()
        # Print the error message for the user
        print("Error: {}\nSystem:{}".format(msg, sErr), file=sys.stderr)
        # Is this a fatal error that requires exiting?
        if (bExit):
            sys.exit(2)
        # Otherwise: return the string that has been made
        return "<br>".join(self.loc_errStack)

    def get_error_message(self):
        """Retrieve just the error message and the line number itself as a string"""

        arInfo = sys.exc_info()
        if len(arInfo) == 3:
            sMsg = str(arInfo[1])
            if arInfo[2] != None:
                sMsg += " at line " + str(arInfo[2].tb_lineno)
            return sMsg
        else:
            return ""

    def get_error_stack(self):
        return " ".join(self.loc_errStack)


class TranslitChe(object):
    is_latin = re.compile(r"[a-zA-Z'-]")
    lst_trans_c = []
    lst_trans_v = []
    diphthongs_full = False
    vowels_macron = False
    # All vowels...
    # - cyr     = normal cyrillic rendering
    # - open    = open syllable with macron rendering
    # - j       = after syllable-starting 'j'
    # - open_j  = open j-starting syllable with macron rendering
    # - g       = after syllable-starting glottal stop
    # - open_g  = open glottal-stop-starting syllable with macron rendering
    # - dip     = diphthong rendering *only in open syllables*
    lst_trans_vs = [
        {'lat': 'aa', 'syl': 'VV', 'cyr': 'а',  'open': 'ā', 'j': 'я', 'open_j': 'я̄'},
        {'lat': 'ae', 'syl': 'V',  'cyr': 'аь',              'j': 'яь'              },
        {'lat': 'a',  'syl': 'V',  'cyr': 'а',               'j': 'я'               },
        {'lat': 'ee', 'syl': 'VV', 'cyr': 'е',  'open': 'ē', 'g': 'э', 'open_g': 'э̄'},
        {'lat': 'eE', 'syl': 'VV', 'cyr': 'ē',               'g': 'э̄'               },
        {'lat': 'e',  'syl': 'V',  'cyr': 'е',               'g': 'э'               },
        {'lat': 'ie', 'syl': 'D',  'cyr': 'е',  'dip': 'иэ', 'g': 'э'               },
        {'lat': 'ii', 'syl': 'VV', 'cyr': 'ий'                                      },
        {'lat': 'i',  'syl': 'V',  'cyr': 'и'                                       },
        {'lat': 'oo', 'syl': 'VV', 'cyr': 'о',  'open': 'ō'                         },
        {'lat': 'oe', 'syl': 'D',  'cyr': 'оь'                                      },
        {'lat': 'o',  'syl': 'V',  'cyr': 'о'                                       },
        {'lat': 'uo', 'syl': 'D',  'cyr': 'о',  'dip': 'уо'                         },
        {'lat': 'uu', 'syl': 'VV', 'cyr': 'у',  'open': 'ȳ', 'j': 'ю', 'open_j': 'ю̄'},
        {'lat': 'u',  'syl': 'V',  'cyr': 'у',               'j': 'ю'               },
        {'lat': 'yy', 'syl': 'VV', 'cyr': 'уьй',             'j': 'юьй'             },
        {'lat': 'ye', 'syl': 'D',  'cyr': 'оь'                                      },
        {'lat': 'y',  'syl': 'V',  'cyr': 'уь',              'j': 'юь'              },
        ]
    oErr = ErrHandle()

    def __init__(self, **kwargs):
        # Read the list of CONSONANTS into my own list
        for item in lst_latin_c:
            arItem = item.split("_")
            oItem = dict(lat=arItem[0], syl=arItem[1], cyr=arItem[2])
            self.lst_trans_c.append(oItem)

        # Make sure to also do what belongs to this object
        return super(TranslitChe, self).__init__(**kwargs)

    def lat2cyr_word(self, sWord):
        """Perform conversion latin to cyrillic on ONE WORD only"""

        def skip_vowel(jPos, sText):
            for item in self.lst_trans_vs:
                sLat = item['lat']
                lenItem = len(sLat)
                if sText[jPos:jPos+lenItem] == sLat:
                    # Found it!
                    return jPos + lenItem, item
            # DIdn't find it
            return jPos, None

        def get_cons(jPos, sText):
            """Get one consonant (cluster)"""

            for item in self.lst_trans_c:
                sLat = item.get('lat')
                lenItem = len(sLat)
                if sText[jPos:jPos+lenItem] == sLat:
                    # Found it!
                    return jPos + lenItem, item
            # DIdn't find it
            return jPos, None

        def get_syl_type(prec_env, syl_this, foll_env, foll_foll_env):
            """Determine the syllable type"""

            sType = "any"
            if syl_this in ['VV', 'D']:
                if foll_env in ['#', 'CC'] or foll_env == "C" and foll_foll_env in ['#', 'C', 'CC'] :
                    sType = "close"
                else:
                    sType = "open"
            return sType

        def get_g_start(prec_env, prec_letter):
            """Determine whether the syllable starts with a glottal stop"""
            bResult = False
            if prec_env == "#" or prec_letter == "'":
                bResult = True
            return bResult

        def capital_type(sWord):
            """Determine the kind of capitalization: none, first, whole"""

            lenWord = len(sWord)
            bFirst = (sWord[0] in lat_upper)
            if not bFirst:
                result = "none"
            else:
                result = "first"
                capCount = 1
                for char in sWord[1:]:
                    if char in lat_upper: capCount += 1
                    if capCount >= 2:
                        result = whole
                        break
            return result

        sBack = ""
        lWord = []
        iPos = 0
        num = len(sWord)
        lBack = []    # The transliterated word we are sending back
        try:
            # Determine the capital type
            capitalization = capital_type(sWord)
            # Now take the lower-case variant
            sWord = sWord.lower()
            # Walk the whole word
            while iPos < num:
                # Skip any vowels
                if sWord[iPos] in vowel_lat:
                    iPos, oVowel = skip_vowel(iPos, sWord)
                    if oVowel == None:
                        # Something went wrong
                        iStop = 1
                    else:
                        lWord.append(oVowel)
                else:
                    # This is a consonant: find it
                    iPos, oCons = get_cons(iPos, sWord)
                    if oCons == None:
                        # Something went wrong
                        iStop = 1
                    else:
                        lWord.append(oCons)
            ## Adapt the syllable of the last one
            #lWord[-1]['syl'] += "#"

            # Second pass: perform the translation into cyrillic
            prec_env = "#"
            prec_letter = ""
            word_len = len(lWord)
            for idx, oLetter in enumerate(lWord):
                # Make sure we have the complete environment
                syl_this = oLetter['syl']
                foll_env = "#" if idx >= word_len-1 else lWord[idx+1]['syl']
                foll_foll_env = "#" if idx >= word_len-2 else lWord[idx+2]['syl']

                # Determine the syllable type: open or closed
                syl_type = get_syl_type(prec_env, syl_this, foll_env, foll_foll_env)

                # Start with a simple case
                if oLetter['syl'] in ['C', 'CC']:
                    # Just produce the cyrillic output
                    lBack.append(oLetter['cyr'])
                elif oLetter['syl'] == "D":
                    # Diphthong...
                    if self.diphthongs_full and 'dip' in oLetter and syl_type == "open":
                        lBack.append(oLetter['dip'])
                    elif 'g' in oLetter and get_g_start(prec_env, prec_letter):
                        lBack.append(oLetter['g'])
                    else:
                        lBack.append(oLetter['cyr'])
                elif oLetter['syl'] == "V":
                    # Short vowel...
                    if prec_letter == "j" and 'j' in oLetter:
                        # Replace with preceding variant
                        lBack[-1] = oLetter['j']
                    elif 'g' in oLetter and get_g_start(prec_env, prec_letter):
                        # Use the glottal-start variant
                        lBack.append(oLetter['g'])
                    else:
                        lBack.append(oLetter['cyr'])
                elif oLetter['syl'] == "VV":
                    # Long vowel
                    if self.vowels_macron and 'open' in oLetter and syl_type == "open":
                        if prec_letter == "j" and 'open_j' in oLetter:
                            # Replace with preceding variant
                            lBack[-1] = oLetter['open_j']
                        elif 'open_g' in oLetter and get_g_start(prec_env, prec_letter):
                            # Use the glottal-start variant
                            lBack.append(oLetter['open_g'])
                        else:
                            lBack.append(oLetter['open'])
                    elif prec_letter == "j" and 'j' in oLetter:
                        # Replace with preceding variant
                        lBack[-1] = oLetter['j']
                    elif 'g' in oLetter and get_g_start(prec_env, prec_letter):
                        # Use the glottal-start variant
                        lBack.append(oLetter['g'])
                    else:
                        lBack.append(oLetter['cyr'])
                else:
                    # Cannot happen
                    self.oErr.Status("lat2cyr_word: unknown syllable type {}".format(oLetter['syl']))

                # Adapt the prec_env (preceding environment) and the prec_letter (preceding letter)
                prec_env = syl_this
                prec_letter = oLetter['lat']
            # COmbine
            sBack = "".join(lBack)
            # Possibly apply capitalization
            if capitalization == "first":
                sBack = sBack[0].capitalize() + sBack[1:]
            elif capitalization == "whole":
                sBack = sBack.capitalize()
        except:
            msg = self.oErr.get_error_message()
            self.oErr.DoError("lat2cyr_word")

        return sBack
   
    def do_lat2cyr(self, sPart, options=None):
        """COnvert latin in [sPart] to cyrillic"""

        # Get the list of switches
        switches = [] if not 'switches' in options else options['switches']
        self.diphthongs_full = (options.get("diphthong") == "full") 
        self.vowels_macron = (options.get("vowel") == "macron")
        
        # Initialize
        bCons = True        # Start of word is with a consonant (if anything, then glottal stop by default)
        iPos = 0            # Position of current Latin letter in word
        iLen = len(sPart)   # Length of the Latin word
        result = []         # The result is a list of objects, one for each phoneme
        bWord = False
        iStart = 0

        try:

            # Divide the string into words
            while iPos < iLen:
                # Are we starting a word or not?
                sThis = sPart[iPos]
                bThisWord = (self.is_latin.match(sThis) != None)
                if iPos == 0 and bThisWord: 
                    bWord = True
                # Check where we are
                if not bWord and bThisWord:
                    # we were inside a non-word, but this is a word...
                    sChunk = sPart[iStart:iPos]
                    # (1) Add chunk to result
                    result.append(sChunk)
                    # (2) Reset counter
                    iStart = iPos
                elif bWord and (not bThisWord or iPos == iLen-1 ):
                    # we were in word, now in non-word
                    if iPos == iLen-1:
                        sWord = sPart[iStart:].strip()
                    else:
                        sWord = sPart[iStart:iPos].strip()
                    # (1) Convert this word
                    converted = self.lat2cyr_word(sWord)
                    # (2) Add word to result
                    result.append(converted)
                    # (3) Reset counter
                    iStart = iPos
                # Make sure we adapt where we are
                bWord = bThisWord

                # Go to the next position
                iPos += 1
            # Re-combine everything
            sPart = "".join(result)

        except:
            msg = self.oErr.get_error_message()
            self.oErr.DoError("do_lat2cyr")

        # Return the result
        return sPart

    def do_lat2phm(self, sPart, options=None):
        """Transliterate from Latin-Academic Chechen to phonemic Chechen"""

        # Initializations
        bOld = False

        # Get the list of switches
        switches = [] if not 'switches' in options else options['switches']
        bGeminateV = ('vv' in switches)
        bGeminateC = ('cc' in switches)
        bIngush = ('ingush' in switches)
        bHw = ('hw' in switches)
        bGh = ('gh' in switches)
        bIpa = ('ipa' in switches)

        try:

            # Treat the 'w' where it is a hw occurring after: c, ch, k, p, sh, s, t
            sPart = re.sub(r"(ch|c|k|p|sh|s|t)w", r"\g<1>ħ",sPart)

            if bGeminateC:
                # Treat 'ww'
                sPart = sPart.replace("ww", "ʕʕ")
                if not bGh:
                    # Convert gh > ʁ (long and short variant)
                    sPart = sPart.replace("ggh", "ʁː").replace("gh", "ʁ").replace("Gh", "ʁ")
                # Convert ch > č (long and short variant)
                sPart = sPart.replace("cch", "čč").replace("ch", "č").replace("Ch", "č")
                # Convert zh > ž (long and short variant)
                sPart = sPart.replace("zzh", "žž").replace("zh", "ž").replace("Zh", "ž")
                # Convert sh > š (long and short variant)
                sPart = sPart.replace("ssh", "šš").replace("sh", "š").replace("Sh", "š")
                if not bHw:
                    # Convert hw > ħ (long and short variant)
                    sPart = sPart.replace("hhw", "ħħ").replace("hw", "ħ").replace("Hw", "ħ")
            else:
                # Treat 'ww'
                sPart = sPart.replace("ww", "ʕː")
                if not bGh:
                    # Convert gh > ʁ (long and short variant)
                    sPart = sPart.replace("ggh", "ʁː").replace("gh", "ʁ").replace("Gh", "ʁ")
                # Convert ch > č (long and short variant)
                sPart = sPart.replace("cch", "čː").replace("ch", "č").replace("Ch", "č")
                # Convert zh > ž (long and short variant)
                sPart = sPart.replace("zzh", "žː").replace("zh", "ž").replace("Zh", "ž")
                # Convert sh > š (long and short variant)
                sPart = sPart.replace("ssh", "šː").replace("sh", "š").replace("Sh", "š")
                if not bHw:
                    # Convert hw > ħ (long and short variant)
                    sPart = sPart.replace("hhw", "ħː").replace("hw", "ħ").replace("Hw", "ħ")
            # Treat the 'w' where it occurs in other places
            sPart = re.sub(r"[Ww]", r"ʕ",sPart)
            # Treat double glottal stop
            if bGeminateC:
                sPart = sPart.replace("''", "ʔʔ")
                sPart = sPart.replace("’’", "ʔʔ")
            else:
                sPart = sPart.replace("''", "ʔː")
                sPart = sPart.replace("’’", "ʔː")
            # Treat single glottal stop
            sPart = re.sub(r"([aeiuoy])(['’])", r"\g<1>ʔ", sPart)
            # Treat [rh]
            sPart = sPart.replace("rh", "r̥")

            # The [v] does NOT change!!!
    
            # Make sure that ejectives have the correct apostrophe
            sPart = sPart.replace("'", "’")
            if bGeminateV:
                if not bIngush:
                    sPart = sPart.replace("Yy", "üː").replace("yy", "üː")
            else:
                # Long vowels
                sPart = sPart.replace("Aa", "aː").replace("aa", "aː")
                sPart = sPart.replace("Ee", "eː").replace("ee", "eː")
                sPart = sPart.replace("Ii", "iː").replace("ii", "iː")
                sPart = sPart.replace("Oo", "oː").replace("oo", "oː")
                sPart = sPart.replace("Uu", "uː").replace("uu", "uː")
                if not bIngush:
                    sPart = sPart.replace("Yy", "üː").replace("yy", "üː")
            # Diphthong
            if bOld:
                sPart = sPart.replace("Ye", "üe").replace("ye", "üe")
                sPart = sPart.replace("Oe", "üe").replace("oe", "üe")   # So /ye/ and /oe/ coincide
                sPart = sPart.replace("Ov", "ou").replace("ov", "ou")
                sPart = sPart.replace("Ev", "eü").replace("ev", "eü")
                sPart = sPart.replace("Av", "au").replace("av", "au")
            else:
                sPart = re.sub(r"Ye(?:^[aeiouy])", r"üe", sPart)
                sPart = re.sub(r"Oe(?:^[aeiouy])", r"üe", sPart)
                sPart = re.sub(r"Ov(?:^[aeiouy])", r"ou", sPart)
                sPart = re.sub(r"Ev(?:^[aeiouy])", r"eü", sPart)
                sPart = re.sub(r"Av(?:^[aeiouy])", r"au", sPart)
                sPart = re.sub(r"ye(?:^[aeiouy])", r"üe", sPart)
                sPart = re.sub(r"oe(?:^[aeiouy])", r"üe", sPart)
                sPart = re.sub(r"ov(?:^[aeiouy])", r"ou", sPart)
                sPart = re.sub(r"ev(?:^[aeiouy])", r"eü", sPart)
                sPart = re.sub(r"av(?:^[aeiouy])", r"au", sPart)
                pass
            # SHort vowels
            if not bIngush:
                sPart = sPart.replace("Y", "ü").replace("y", "ü")
            # Long consonants
            if not bGeminateC:
                sPart = sPart.replace("bb", "bː").replace("dd", "dː").replace("gg", "gː")
                sPart = sPart.replace("hh", "hː").replace("kk", "kː").replace("ll", "lː")
                sPart = sPart.replace("mm", "mː").replace("nn", "nː").replace("pp", "pː")
                sPart = sPart.replace("qq", "qː").replace("rr", "rː").replace("ss", "sː")
                sPart = sPart.replace("tt", "tː").replace("vv", "vː").replace("xx", "xː")
                sPart = sPart.replace("zz", "zː")

            # Should we do IPA?
            if bIpa:
                sPart = sPart.replace("ü", "y")
                sPart = sPart.replace("š", "ʃ")
                sPart = sPart.replace("ž", "ʒ")
                sPart = sPart.replace("č", "ʧ")
                sPart = sPart.replace("c", "ʦ")
                sPart = sPart.replace("x", "χ")

        except:
            msg = self.oErr.get_error_message()
            self.oErr.DoError("do_lat2phm")

        # Return the result
        return sPart
