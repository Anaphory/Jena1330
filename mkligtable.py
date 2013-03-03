#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Read the files from the specified sfdir directory, generating a
ligtable to drop into a tftopl generated pl file."""

import sys
import os
import re

def between(string, left='"', right=None, start=0):
    if right is None:
        right = left
    left = string.index(left, start)+1
    return string[left : string.index(right, left)]

class ChainSub (object):
    def __init__(self):
        self.classes = []
        self.bclasses = []
        self.fclasses = []
        self.substitutions = [] #A list of quadruplets, each
                                #quadruplet consisting of an index to
                                #classes, an index to bclasses, an
                                #index to fclasses and a substitution
                                #subtable.
    def lookahead(self):
        lookaheads = {}
        for c, bc, fc, table in self.substitutions:
            if bc is None:
                for glyph in self.classes[c]:
                    subs = lookaheads.setdefault(
                        glyph, {})
                    for forward in self.fclasses[fc]:
                        subs[forward] = (
                            substitutions[
                                table + " subtable"
                                ][glyph])
        return lookaheads
    def lookbehind(self):
        lookbehinds = {}
        for c, bc, fc, table in self.substitutions:
            if fc is None:
                for glyph in self.classes[c]:
                    for backward in self.bclasses[bc]:
                        subs = lookbehinds.setdefault(
                            backward, {})
                        subs[glyph] = (
                            substitutions[
                                table + " subtable"
                                ][glyph])
        return lookbehinds
                
                

        
def ligtable(
    internals,
    substitutions,
    lookaheads,
    lookbehinds,
    ligatures,
    kernings,
    boundary_characters = ".,;:()-!?"
    ):
    bchar = max(set(range(256))-set(internals))

    #Bring data in a form we can use to write the ligtable
    init = {}
    fina = {}
    interesting_glyphs = set()
    #"Interesting" are those glyphs that have ligature
    #or kerning data associated with them.
    for name, table in substitutions.items():
        if "'init'" in name:
            init.update(table)
        elif "'fina'" in name:
            fina.update(table)
            interesting_glyphs.update(set(table))

    liga = {}
    for name, table in ligatures.items():
        liga.update(table)
        interesting_glyphs.update(set(table))

    kern = {}
    for name, table in kernings.items():
        kern.update(table)
        interesting_glyphs.update(set(table))

    interesting_glyphs.update(lookaheads)
    interesting_glyphs.update(lookbehinds)

    boundary_characters = [
        positions[unicodes[ord(boundary_character)]]
        for boundary_character in boundary_characters] + [
        bchar]


    #Replace references to 'usual' glyphs by their medial and historic
    #forms in the encoding tables.

    #Start writing the ligtable:
    #It starts with a boundarychar.
    print("(BOUNDARYCHAR O %o)" % bchar)
    print("(LIGTABLE");
    print("  (LABEL BOUNDARYCHAR)")
    for general, initial in init.items():
        print("   (LIG O %o O %o)" % (
            positions[general],
            positions[initial]))
    print("  (STOP)")

    #Deal with init forms.
    #These are lookbehind contextuals, therefor "/LIG"
    for boundary_character in boundary_characters:
        print("  (LABEL O %o)" % boundary_character)
        for general, initial in init.items():
            print("   (/LIG O %o O %o)" % (
                positions[general],
                positions[initial]))
        print("  (STOP)")
        
    #Deal with other glyphs.
    for glyph in interesting_glyphs:
        print("  (LABEL O %o)" % positions[glyph])
        for lookbehind, to in lookbehinds.get(
            glyph, {}).items():
            print("   (/LIG O %o O %o)" % (
                positions[lookbehind],
                positions[to]))
        for lookahead, to in lookaheads.get(
            glyph, {}).items():
            print("   (LIG/ O %o O %o)" % (
                positions[lookahead],
                positions[to]))
        if glyph in fina:
            for boundary_character in boundary_characters:
                print("   (LIG/ O %o O %o)" % (
                    boundary_character,
                    positions[fina[glyph]]))
        for ligother, to in liga.get(
            glyph, {}).items():
            print("   (LIG O %o O %o)" % (
                positions[ligother],
                positions[to]))
        for kernother, amount in kern.get(
            glyph, {}).items():
            print("   (KRN O %o R %f)" % (
                positions[internals[kernother]],
                amount*0.001))
        print("  (STOP)")
    print(" )")
            
    
#if __name__=="__main__":
#    directory = sys.argv[1]
if True:
    directory = "Jena1330.sfdir"

    fontprops = os.path.join(directory, "font.props")
    lookups = []
    chainsubs = []
    kernings = {}
    substitutions = {}
    ligatures = {}
    chainsub = None
    with open(fontprops) as propsfile:
        for line in propsfile:
            line = line.strip()
            if line.startswith("Lookup"):
                #This defines a Lookup table.
                #Save its name in lookups.
                lookups.append(between(line, '"'))
            elif line.startswith("ChainSub2"):
                #Chain Substitution header
                #If there is a current chaining substitution table, append it to their list.
                if chainsub:
                    chainsubs.append(chainsub)
                chainsub = ChainSub()
            elif line.startswith("Class"):
                #Line defines a substitution class for the current
                #ChainSub. The first and second word are the
                #"Class:" and a number, the class elements are
                #words 2:.
                chainsub.classes.append(line.split()[2:])
                #Yes, this line is expected to throw an
                #AttributeError in some cases.
                
            elif line.startswith("BClass"):
                #Line defines a lookbehind class for the current
                #ChainSub, similar to "Class".
                chainsub.bclasses.append(line.split()[2:])
            elif line.startswith("FClass"):
                #Line defines a lookforward class for the current
                #ChainSub, similar to "Class".
                chainsub.fclasses.append(line.split()[2:])
            elif line.startswith("ClsList"):
                items = line.split()
                if len(items)==1:
                    raise ValueError(
                        "ClsList was empty."
                        )
                elif len(items)==2:
                    classlist_index = int(items[1])-1
                    # FontForge Class indices are 1-based,
                    # Python list indices are 0-based
                else:
                    raise NotImplementedError(
                            "Program does not cope with multiple classes yet."
                            )
            elif line.startswith("BClsList"):
                items = line.split()
                if len(items)==1:
                    bclasslist_index = None
                elif len(items)==2:
                    bclasslist_index = int(items[1])-1
                else:
                    raise NotImplementedError(
                            "Program does not cope with multiple classes yet."
                            )
            elif line.startswith("FClsList"):
                items = line.split()
                if len(items)==1:
                    fclasslist_index = None
                elif len(items)==2:
                    fclasslist_index = int(items[1])-1
                else:
                    raise NotImplementedError(
                            "Program does not cope with multiple classes yet."
                            )
            elif line.startswith("SeqLookup"):
                #Line defines what do do for the current case for this
                #ChainSub.  We are supposed to know the lookup
                #referenced here
                substitution = between(line, '"')
                assert(substitution in lookups)
                #This and the classlists form a new chain substitution
                #item. Save it in the chain substitutions.
                chainsub.substitutions.append(
                    (classlist_index,
                     bclasslist_index,
                     fclasslist_index,
                     substitution))
            else:
                #Line is not particularly important, ignore.
                pass
            
    positions = {}
    unicodes = {}
    internals = {}
    for glyph in os.listdir(directory):
        if glyph.endswith(".glyph"):
            with open(
                os.path.join(directory, glyph)
                ) as glyphfile:
                glyphname = None
                for line in glyphfile:
                    line = line.strip()
                    if line.startswith("StartChar:"):
                        glyphname = line.split()[1]
                    if line.startswith("Encoding:"):
                        # Encoding lines contain three numbers: The
                        # code point as by the encoding defined in the
                        # font.props, the Unicode code point and an
                        # internal encoding.
                        (_,
                         position,
                         unic,
                         internal) = line.split()
                        positions[glyphname] = int(position)
                        if unic != "-1":
                            unicodes[int(unic)] = glyphname
                        internals[int(internal)] = glyphname
                            
                    if line.startswith("Substitution2:"):
                        table = substitutions.setdefault(
                            between(line, '"'),
                            {})
                        substitute_to = line.split()[-1]
                        table[glyphname] = substitute_to
                    if line.startswith("Kerns2:"):
                        #decompose the line into data, table pairs
                        blobs = line[len("Kerns2:"):]
                        blobs = blobs.split('"')
                        #Do not have '"' in table names, as it would
                        #break this!!!!
                        blobs = list(zip(blobs[::2], blobs[1::2]))
                        
                        for data, tablename in blobs:
                            table = kernings.setdefault(
                                tablename,
                                {})
                            kern = table.setdefault(
                                glyphname,
                                {})
                            other, kerning = data.split()
                            kern[int(other)] = int(kerning)
                    if line.startswith("Ligature2:"):
                        table = ligatures.setdefault(
                            between(line, '"'),
                            {})
                        start = line.index('"', line.index('"')+1)
                        components = line[start+1:].split()
                        if len(components)>2:
                            raise NotImplementedError
                        lig = table.setdefault(
                            components[0],
                            {})
                        lig[components[1]]=glyphname
    ligtable(internals,
             substitutions,
             chainsub.lookahead(),
             chainsub.lookbehind(),
             ligatures,
             kernings
             )
             

                        
