import os
import shutil
import xmlrunner
import unittest
import coverage


def main():
    test_dir = 'test-output'
    cover_dir = f'{test_dir}/coverage'
    main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    test_output = os.path.join(main_dir, test_dir)
    cover_output = os.path.join(main_dir, cover_dir)

    # Force using testing.ini
    os.environ["TEST"] = "1"

    # Remove old unittest reports.
    shutil.rmtree(test_output, ignore_errors=True)

    # Start coverage tests.
    coverage_tester = coverage.coverage(
        source=['todos'],
    )
    coverage_tester.start()

    # Run unit tests.
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output=test_output),
        # these make sure that some options that are not applicable
        module=None, failfast=False, buffer=False, catchbreak=False, exit=False
    )

    # Generate coverage report.
    print('Generating coverage reports...')
    coverage_tester.stop()
    coverage_tester.save()
    coverage_tester.html_report(directory=cover_output)
    print(f'Coverage report generated at {cover_dir}/index.html')
    coverage_tester.erase()


if __name__ == '__main__':
    main()
