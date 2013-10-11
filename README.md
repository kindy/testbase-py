
Implement Perl's Test::Base *parser* in Python

http://search.cpan.org/~ingy/Test-Base-0.60/lib/Test/Base.pm

```python
import testbase

print testbase.parse('''
    === abc x 
    --- a md5
    xadf  

    --- b b64e
    yadf 
    --- c b64e b64d len add=-6 add=10
    yadf 

    === abc
    --- a: xadf
    --- b
    yadf
    --- c jsond
    {
    "a": 123,
    "b": 456
    }
    ''')
```

Output:

```python
[{'a': 'e45d1a72235ae0e1b8a56b427cb3a8aa', 'c': 8, 'b': 'eWFkZg==', 'name': 'abc x', 'desc': 'abc x'}, {'a': 'xadf', 'c': {'a': 123, 'b': 456}, 'b': 'yadf', 'name': 'abc', 'desc': 'abc'}]
```

