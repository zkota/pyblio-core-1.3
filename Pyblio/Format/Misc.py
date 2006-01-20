from Pyblio.Format.DSL import lazy

def plural (record, sequence, zero = None, one = None, two = None, more = ''):
    """
    Generate different outputs depending on the number of items in the sequence.
    
    @param sequence:
        The sequence whose item count will be used to generate the output.
    @type  sequence:
        list

    @param zero:
        value returned when the sequence is empty
    @param one:
        value returned when the sequence has one item
    @param two:
        value returned when the sequence has two items
    @param more:
        value returned when the sequence has more than two items

    @note when a given parameter is not provided but should be returned,
      then the default is to use the value of the L{more} parameter.
    """

    l = len (sequence(record))
    
    if l == 0 and zero is not None:
        return zero(record)
    elif l == 1 and one is not None:
        return one(record)
    elif l == 2 and two is not None:
        return two(record)
    else:
        return more(record)

plural = lazy (plural)