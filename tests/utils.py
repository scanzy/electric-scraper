import typing as t


def RunTests(funcName: str, func: t.Callable, testCases: list[tuple[list, t.Any]]) -> bool:
    """Runs all test cases for a function and displays results.
    Every test case is a tuple of arguments (list) and expected result.
    If expected result is an exception type, the case should raise that exception.
    Returns True if all tests passed, False otherwise.
    """
    print(f"\n=== Tests for '{funcName}' ===")
    
    passed = 0
    total = len(testCases)
    
    # for each test case
    for i, testCase in enumerate(testCases):
        caseNumber = i + 1

        # gets arguments and expected result
        args, expected = testCase
        
        # negative test case, should raise an exception
        if isinstance(expected, type) and issubclass(expected, Exception):
            try:
                result = func(*args)
    
                # incorrect: exception not raised
                print(f"✗ Case {caseNumber}: {args[0]} -> Should raise {expected.__name__} but returned {result}")

            # correct: exception raised and matches expected
            except Exception as e:
                if isinstance(e, expected):
                    print(f"✓ Case {caseNumber}: {args[0]} -> {type(e).__name__} correctly raised")
                    passed += 1
                
                # incorrect: exception raised but does not match expected
                else:
                    print(f"✗ Case {caseNumber}: {args[0]} -> Unexpected {type(e).__name__}: {e}")

        # positive test case, should return a result
        else:
            try:
                result = func(*args)

                # correct: result matches expected
                if result == expected:
                    print(f"✓ Case {caseNumber}: {args[0]} -> {result}")
                    passed += 1

                # incorrect: result does not match expected
                else:
                    print(f"✗ Case {caseNumber}: {args[0]} -> {result} (expected: {expected})")
                
            # incorrect: exception raised
            except Exception as e:
                print(f"✗ Case {caseNumber}: {args[0]} -> Unexpected {type(e).__name__}: {e}")
    
    print(f"Result: {passed}/{total} tests passed")
    return passed == total
