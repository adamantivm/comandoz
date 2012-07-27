fn=5k_words_repeats
text2idngram -vocab $fn.vocab -idngram $fn.idngram < $fn.txt
idngram2lm -vocab_type 0 -idngram $fn.idngram -vocab $fn.vocab -arpa $fn.0.lm
idngram2lm -vocab_type 1 -idngram $fn.idngram -vocab $fn.vocab -arpa $fn.1.lm
idngram2lm -vocab_type 2 -idngram $fn.idngram -vocab $fn.vocab -arpa $fn.2.lm
