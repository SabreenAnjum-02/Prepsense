# Python Interview Guide

## Topic: Generators
Generators are functions that return an iterable set of items, one at a time, in a special way. 
When an iteration over a set of items starts using the `yield` statement, the function pauses its execution and sends the yielded value to the caller. 
When the function is resumed, it continues execution immediately after the last yield run. This allows the generator to produce items over time, rather than computing them all at once and sending them back like a list.

## Topic: Decorators
A decorator in Python is any callable Python object that is used to modify a function or a class. A reference to a function "func" or a class "C" is passed to a decorator and the decorator returns a modified function or class. The modified functions or classes usually contain calls to the original function "func" or class "C".
