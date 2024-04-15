import os
import subprocess
from process_response import remove_package_references


def compile_code(code, java_file_path, package_name, dependency_file_path=''):
    with open(java_file_path, 'w+') as file:
        file.write(remove_package_references(code, package_name))
    compile_command = subprocess.Popen(
        f'javac -cp junit/junit-platform-console-standalone-1.8.2.jar {java_file_path} {dependency_file_path}',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'javac -cp junit/junit-platform-console-standalone-1.8.2.jar {dependency_file_path} {java_file_path}')
    return compile_command


def run_code(class_name):
    run_command = subprocess.Popen(
        f'java -javaagent:jacoco/jacocoagent.jar=destfile=report/{class_name}.exec '
        f'-jar junit/junit-platform-console-standalone-1.8.2.jar --class-path java --select-class {class_name}',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'java -javaagent:jacoco/jacocoagent.jar=destfile=report/{class_name}.exec '
          f'-jar junit/junit-platform-console-standalone-1.8.2.jar --class-path java --select-class {class_name}')
    return run_command


def generate_jacoco_report(class_name):
    report_command = subprocess.Popen(
        f'java -jar jacoco/jacococli.jar report report/{class_name}.exec --classfiles java --csv '
        f'report/{class_name}.csv', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'java -jar jacoco/jacococli.jar report report/{class_name}.exec --classfiles java --csv '
          f'report/{class_name}.csv')
    return report_command


def get_code_coverage(class_name):
    sum_instructions_and_covered = "{ instructions += $4 + $5; covered += $5 }"
    divide_covered_over_instructions = '{ print 100*covered/instructions }'
    report_command = subprocess.Popen(
        f'awk -F, \'$3=="{class_name.replace("Test", "")}" {sum_instructions_and_covered} END '
        f'{divide_covered_over_instructions}\' report/{class_name}.csv',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'awk -F, \'3=="{class_name.replace("Test", "")}" {sum_instructions_and_covered} END '
          f'{divide_covered_over_instructions}\' report/{class_name}.csv'
          )
    return report_command


def indent_code(code, java_file_path):
    with open(java_file_path, 'w+') as file:
        file.write(code)
    indent_command = subprocess.Popen(
        f'java -jar format/google-java-format-1.21.0-all-deps.jar {java_file_path}', shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return indent_command


def delete_generated_files(class_name):
    file_paths = [
        f'java/{class_name}.java',
        f'java/{class_name}Test.java',
        f'java/{class_name}.class',
        f'java/{class_name}Test.class',
        f'report/{class_name}Test.exec',
        f'report/{class_name}Test.csv'
    ]

    for file_path in file_paths:
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass
