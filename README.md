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
NiceScript _strictly_ uses indentation to indicate block statements.
The currently limited grammar includes three types of statements:
#### Identifiers
Identifiers (represented as `NAME`) is anything that matches the following regex: `[a-zA-Z_$#][a-zA-Z0-9_$#\.]*`, or in words:
An identifier can start with any letter, underscore, dollar, and hash sign.
An identifier can continue with any alphanumeric character, underscore, dollar, hash sign, and period.
#### Variable definitions/changes
Variable definitions and changes take the form `NAME = EXPRESSION`.
#### If statements
If statements take the form `if EXPRESSION` or `if EXPRESSION COMPARISON EXPRESSION`, if statements must be followed by indented code, the statement stops on unindentation.
Comparisons can be `=` (js `===`,) `!=` (js `!==`,) `>`, `>=`, `<`, or `<=`.
#### Function definitions
Lambdas can be written inline, or block.
Inline Lambdas take the form `ARGUMENTS -> EXPRESSION`, where `ARGUMENTS` are identifiers seperated by whitespace.
Block Lambdas take the form `ARGUMENTS ->`, followed by a block statement.
#### Function calls
Function calls are similar to simplified ruby or elixir function calls: `FUNCTIONNAME ARGUMENTS`, where `ARGUMENTS` are expressions seperated by whitespace.
Function calls without arguments can be done with just the name by itself.
#### Types
There are currently only three types: `NUMBER`, `STRING`, and `REGEX`.
### Alternative tokens
NiceScript has plenty of alternative tokens for mathamatical expressions. the complete list is:
- `with`, `and`, and `plus` instead of `+`
- `without`, and `minus` instead of `-`
- `times`, and `by` instead of `*`
- `on`, and `over` instead of `/`
- `mod`, and `modulo` instead of `%`
- `is` instead of `=`
- `is not` instead of `!=`
- `is more than` instead of `>`
- `is less than` instead of `<`
- `is more than or equal to` instead of `>=`
- `is less than or equal to` instead of `<=`
### Built in functions
NiceScript currently has 4 built in functions (including their JavaScript equivalents):
- `print` becomes `console.log`
- `printerror` becomes `console.error`
- `skip` becomes `continue;`
- `break` stays as `break;`
### Example programs
FizzBuzz (Console output):
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
Fibonacci:
```
fibonacci = index ->
    if index < 2
        return index
    return (fibbonachi (index - 1)) + (fibbonachi (index - 2)) /* Parens so it becomes fib(i-2) and not fib(i,-,2)*/
/* Usage: [fibonacci index] */
number = fibonacci 10 /* 55 */
```
