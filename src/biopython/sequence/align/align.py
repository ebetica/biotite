# Copyright 2017 Patrick Kunzmann.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

from .matrix import SubstitutionMatrix
from ..sequence import Sequence
import numpy as np
import copy


class Alignment():
    
    def __init__(self, seq1, seq2, trace, score):
        self.seq1 = seq1
        self.seq2 = seq2
        self.trace = trace
        self.score = score
    
    def __str__(self):
        pass


def simple_score(seq1, seq2, matrix):
    if len(seq1) != len(seq2):
        raise ValueError("Sequence lengths of {:d} and {:d} are not equal"
                         .format( len(seq1), len(seq2) ))
    if (matrix.alphabet1() != seq1.get_alphabet() and
        matrix.alphabet2() != seq2.get_alphabet()):
            raise ValueError("The sequences' alphabets do not fit the matrix")
    seq1_code = seq1.get_seq_code()
    seq2_code = seq1.get_seq_code()
    score = 0
    for i in range(len(seq1)):
        score += matrix.get_score_by_code(seq1_code[i], seq2_code[i])
    return code


def align_global(seq1, seq2, matrix, gap_opening=-3, gap_extension=-1):
    # This implementation uses transposed tables in comparison
    # to the original algorithm
    # Therefore the first sequence is one the left
    # and the second sequence is at the top  
    # The table for saving the scores
    score_table = np.zeros(( len(seq1)+1, len(seq2)+1 ), dtype="i4")
    # The table the directions a field came from
    # A "1" in the corresponding bit means
    # the field came from this direction
    # The values: bit 1 -> 1 -> diagonal -> alignment of symbols
    #             bit 2 -> 2 -> left     -> gap in first sequence
    #             bit 3 -> 4 -> top      -> gap in second sequence
    trace_table = np.zeros(( len(seq1)+1, len(seq2)+1 ), dtype="u1")
    score_table[:,0] = -np.arange(0, len(seq1)+1)
    score_table[0,:] = -np.arange(0, len(seq2)+1)
    code1 = seq1.get_seq_code()
    code2 = seq2.get_seq_code()
    
    # Fill table
    max_i = score_table.shape[0]
    max_j = score_table.shape[1]
    i = 1
    while i < max_i:
        j = 1
        while j < max_j:
            # Evaluate score from diagonal direction
            from_diag = score_table[i-1, j-1]
            # -1 is necessary due to the shift of the sequences
            # to the bottom/right in the table
            from_diag += matrix.get_score_by_code(code1[i-1], code2[j-1])
            # Evaluate score from left direction
            from_left = score_table[i, j-1]
            if trace_table[i, j-1] & 2:
                from_left += gap_extension
            else:
                from_left += gap_opening
            # Evaluate score from top direction
            from_top = score_table[i-1, j]
            if trace_table[i-1, j] & 2:
                from_top += gap_extension
            else:
                from_top += gap_opening
            # Find maximum
            trace, score = _eval_trace_from_score(from_diag,from_left,from_top)
            score_table[i,j] = score
            trace_table[i,j] = trace
            j +=1
        i += 1
    
    # Traceback
    i = max_i-1
    j = max_j-1
    max_score = score_table[i,j]
    trace = []
    trace_list = []
    _traceback(trace_table, i, j, trace, trace_list)
    trace_list = [np.flip(np.array(tr, dtype=int), axis=0)
                  for tr in trace_list]
    # Remove gap entries in traces
    for i, trace in enumerate(trace_list):
        trace = trace[np.unique(trace[:,0], return_index=True)[1]]
        trace = trace[np.unique(trace[:,1], return_index=True)[1]]
        trace_list[i] = trace
    
    return [Alignment(seq1, seq2, trace, max_score) for trace in trace_list]
    
    
    


def _eval_trace_from_score(from_diag, from_left, from_top):
    if from_diag > from_left:
        if from_diag > from_top:
            return 1, from_diag
        elif from_diag == from_top:
            return 5, from_diag
        else:
            return 4, from_top
    elif from_diag == from_left:
        if from_diag > from_top:
            return 3, from_diag
        elif from_diag == from_top:
            return 7, from_diag
        else:
            return 4, from_top
    else:
        if from_left > from_top:
            return 2, from_left
        elif from_left == from_top:
            return 6, from_diag
        else:
            return 4, from_top


def _traceback(trace_table, i, j, trace, trace_list):
    while trace_table[i,j] != 0:
        # -1 is necessary due to the shift of the sequences
        # to the bottom/right in the table
        trace.append((i-1, j-1))
        # Traces may split
        next_indices = []
        trace_value = trace_table[i,j]
        if trace_value & 1:
            next_indices.append((i-1, j-1))
        if trace_value & 2:
            next_indices.append((i, j-1))
        if trace_value & 4:
            next_indices.append((i-1, j))
        # Trace split -> Recursive call of _traceback() for indices[1:]
        for k in range(1, len(next_indices)):
            new_i, new_j = next_indices[k]
            _traceback(trace_table, new_i, new_j, copy.copy(trace), trace_list)
        # Continue in this method with indices[0]
        i, j = next_indices[0]
    trace_list.append(trace)
