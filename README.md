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
Identifiers are only used for variables.
#### Variable definitions/changes
Variable definitions and changes take the form `NAME = EXPRESSION`.
#### If/Else statements
If statements take the form `if EXPRESSION` or `if EXPRESSION COMPARISON EXPRESSION`, if statements must be followed by a block statement.
Comparisons can be `=` (js `===`,) `!=` (js `!==`,) `>`, `>=`, `<`, or `<=`.
If statements excecute the code if the comparison between the expressions is truthy OR without a comparison, it excecutes the code if the expression by itself is truthy.
Else statements are just `else` on a single line, and must be placed after the block statement. Else statements excecute if the condition specified for the preceeding If statement was falsy.
#### Function definitions
Lambdas can be written inline, or block.
Inline Lambdas take the form `ARGUMENTS -> EXPRESSION`, where `ARGUMENTS` are identifiers seperated by whitespace.
Block Lambdas take the form `ARGUMENTS ->`, followed by a block statement.
Block Lambdas are basically just functions, and Inline Lambdas are basically just one-line functions.
NOTE: You must assign a Lambda to a variable if you want to give it a name.
```
double = x -> x * 2
print (double 9)
/* 18 */
```
#### Function calls
Function calls are similar to simplified ruby or elixir function calls: `FUNCTIONNAME ARGUMENTS`, where `ARGUMENTS` are expressions seperated by whitespace.
Function calls without arguments can be done with just the name by itself.
Function calls just excecute the code specified by the name, although the name is *technically* an expression, so you can do something like this:
```
print ((x -> x * 2) 46)
/* 92 */
```
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
    if ( counter mod 15 ) is 0
        print "FizzBuzz"
        skip
    if ( counter mod 5 ) is 0
        print "Buzz"
        skip
    if ( counter mod 3 ) is 0
        print "Fizz"
        skip
    print counter
```
Compiles to:
```javascript
var counter;
for (counter = 0; counter++ < 100;) {
    if (counter % 15 === 0) {
        console.log('FizzBuzz');
        continue;
    }
    if (counter % 5 === 0) {
        console.log('Buzz');
        continue;
    }
    if (counter % 3 === 0) {
        console.log('Fizz');
        continue;
    }
    console.log(counter);
}
```
Fibonacci:
```
fibonacci = index ->
    if index < 2
        return index
    return (fibonacci (index - 1)) + (fibonacci (index - 2))
    /* Parens so it becomes fib(i-2) and not fib(i,-,2)*/
/* Usage: [fibonacci index] */
number = fibonacci 10
print number
/* 55 */
```
Compiles to:
```javascript
var fibonacci, number;
fibonacci = (index) => {
    if (index < 2) {
        return index;
    }
    return (fibonacci(index - 1)) + (fibonacci(index - 2));
var index;
}
number = fibonacci(10);
console.log(number);
```
