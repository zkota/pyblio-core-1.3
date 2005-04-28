from Pyblio.Format.DSL import lazy

def _year (date):

    return str (date ().year)


year = lazy (_year)
