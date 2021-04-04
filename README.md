# NiceScript
---
NiceScript is a language that compiles to javascript, and aims to have the simplest and most readable grammar possible.
The dependencies.sh and dependencies.bat files are there so you can just download all dependencies without trial and error.
## Compiler Usage
---
```
usage: compile.py [-h] [-o O] in_file

positional arguments:
  in_file     The input nicescript file

optional arguments:
  -h, --help  show this help message and exit
  -o O        The output file. (defaults to a.out)
```
## Syntax
---
### Statements
NiceScript uses indentation to indicate compound statements.
The currently limited grammar includes three types of statements:
##### Variable definitions/changes
Variable definitions and changes take the form `NAME = EXPRESSION`.
##### If statements
If statements take the form `if EXPRESSION` or `if EXPRESSION = EXPRESSION`, if statements must be followed by indented code, the statement stops on unindentation.
##### Function calls
Function calls are similar to simplified ruby or elixir function calls: `FUNCTIONNAME ARGUMENTS`, arguments are expressions seperated by whitespace.
Function calls without arguments can be done with just the name by itself.
### Alternative tokens
NiceScript has plenty of alternative tokens for mathamatical expressions. the complete list is:
- `with`, `and`, and `plus` instead of `+`
- `without`, and `minus` instead of `-`
- `times`, and `by` instead of `*`
- `on`, and `over` instead of `/`
- `mod`, and `modulo` instead of `%`
- `is` instead of `=`
### Built in functions
NiceScript currently has 3 built in functions (including their JavaScript equivilents):
- `print` becomes `console.log`
- `skip` becomes `continue;`
- `break` stays as `break;`
### Example program
This is FizzBuzz in NiceScript
```
counter is from 0 to 100
    if counter mod 15 is 0
		print "FizzBuzz"
		skip
	if counter mod 5 is 0
		print "Buzz"
		skip
	if counter mod 3 is 0
		print "Fizz"
		skip
	print counter
```
