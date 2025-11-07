#!/usr/bin/env python3
"""Demo module for testing self-modification capabilities."""

def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total

def process_data(data):
    try:
        result = data.get('value') * 2
        return result
    except:
        return None
