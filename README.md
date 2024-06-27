# Report for Assignment 1

## Project chosen

Name: **mygpo**

URL: (https://github.com/gpodder/mygpo)

Number of lines of code and the tool used to count it:
**17,266**, counted using **lizard**

Programming language: **Python**

## Coverage measurement

### Existing tool

<Inform the name of the existing tool that was executed and how it was executed>

Since our project was written in python, we used **Coverage.py** to measure the coverage of the tests.

To run the tool, the following steps were taken:

1. Navigate to the cloned **mygpo** directory
2. Run the command: `coverage run --source="*" manage.py test` replacing the `*` with the desired directory (**mygp** if running over the entire project)
3. Run the command `coverage report` to produce a report on the terminal
4. (Optional) Run the command `coverage html` to produce an **html** version of the report

<Show the coverage results provided by the existing tool with a screenshot>

![Initial Coverage Results](coverage/coverage_before.png "Initial Coverage Results")

### Your own coverage tool

<The following is supposed to be repeated for each group member>

#### Hussein Sarrar

<Function 1 name>

##### Function 1: **upload** in **mygpo/api/legacy.py**

<Show a patch(diff) or provide a link to a commit showing the instrumented function>

[Link to commit](https://github.com/gpodder/mygpo/commit/139b0d6521379a7a70e2e83b8d06b106f4c5b096)

**NOTE:** This commit is not the first commit showing the instrumentation, rather a second commit where I expanded coverage to take invisible else clauses into account.


<Provide a screenshot of the coverage results output by the instrumentation>

The function was not being tested initially, and so produced no coverage results.


<Provide the same information for function 2>

###### Function 2: **view_or_basicauth** in **mygpo/userfeeds/auth.py**

[Link to commit](https://github.com/gpodder/mygpo/commit/139b0d6521379a7a70e2e83b8d06b106f4c5b096)

**NOTE:** This commit is not the first commit showing the instrumentation, rather a second commit where I expanded coverage to take invisible else clauses into account.

![View_or_basicauth Coverage Results](coverage/report_images/hussein_v_or_ba_cov_results.png "View_or_basicauth Coverage Results")

#### Mohamed Hussain Shareef

##### Function 1: episode_status_icon in mygpo/web/templatetags/episodes.py

[Link to commit summary (BRANCH INSTRUMENTATION)](https://github.com/HusseinSarrar05/mygpo/pull/4/files#diff-761057704aefb718d8b927b536b11bd3d11541447d027a3d93449dae55e132e4)

The function had 0% coverage initially, so it produced no coverage results. Check below to see the coverage results after:
[Link to commit summary (COVERAGE RESULTS)](https://github.com/HusseinSarrar05/mygpo/pull/4/files#diff-761057704aefb718d8b927b536b11bd3d11541447d027a3d93449dae55e132e4)

Screenshot:
![image](https://github.com/HusseinSarrar05/mygpo/assets/45093174/1fe51550-c8ad-43d8-b693-d30939e2253c)

##### Function 2: EpisodeUpdater in mygpo/data/feeddownloader.py

[Link to commit summary (BRANCH INSTRUMENTATION)](https://github.com/HusseinSarrar05/mygpo/pull/4/files#diff-8c15d9291fda719b8caedcd25c94db3dbdbe1e36f76d43b9254249b58ea5f321)

The function had 0% coverage initially, so it produced no coverage results. Check below to see the coverage results after:
[Link to commit summary (COVERAGE RESULTS)](https://github.com/HusseinSarrar05/mygpo/pull/4/files#diff-f84ea5bd798f6c5f42ba9c634e519bbf37b0999055f209097f5f711561868bde)

Screenshot:
![image](https://github.com/HusseinSarrar05/mygpo/assets/45093174/c1d54295-f1cb-4a7e-8f03-02f00acc74c5)

#### Samuel Power

<Function 1 name>

##### Function 1: **episode_status_text** in mgpo/web/templatetags/episodes.py**

<Show a patch(diff) or provide a link to a commit showing the instrumented function>

[Link to commit](https://github.com/HusseinSarrar05/mygpo/pull/2/commits/e95c9851dc64d98c2d3ad6741954784b647a7085)

**NOTE:** This commit is not the final commit, but the first one where branch coverage is completed. Please navigate to pull request to see full overview of changes for this function.

![View_or_basicauth Coverage Results](coverage/report_images/Samuel_coverage_episodes.png "episode_status_text")

<Provide a screenshot of the coverage results output by the instrumentation>

The function was not being tested initially, and so produced no coverage results.


<Provide the same information for function 2>

###### Function 2: **normalize_feed_url** in **mygpo/utils.py**

[Link to commit](https://github.com/HusseinSarrar05/mygpo/pull/2/commits/cbe2a50c129e3f13be3dfd0dfc3d287acd0cdb24)

**NOTE:** Please note that the function was duplicated for testing purposes, and renamed to normalize_url. This was done because python does not support function overloading, which would have otherwise been necessary due to the functions high number of dependents contained in other files. 

![View_or_basicauth Coverage Results](coverage/report_images/Samuel_coverage_utils.png "normalize_feed_url Coverage Results")


## Coverage improvement

All coverage results were written to **txt** files

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name>

#### Hussein Sarrar

<Test 1>

##### Test for function 1: upload


<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

[Link to commit showing test](https://github.com/gpodder/mygpo/commit/5a18f0d8c9f5c85d0d519091a200da57b221970d),
Test can be found in **mygpo/api/tests.py** file.

<Provide a screenshot of the old coverage results (the same as you already showed above)>

The function was not being tested at all and had 0% coverage.

<Provide a screenshot of the new coverage results>

![Upload Coverage Results](coverage/report_images/hussein_upload_cov_results.png "Upload Coverage Results")

<State the coverage improvement with a number and elaborate on why the coverage is improved>

After creating a new test for it, the coverage achieved was **100%**. All different logical paths through the function were taken, and the results were asserted.

<Test 2>

##### Test for function 2: view_or_basicauth
<Provide the same kind of information provided for Test 1>

[Link to commit showing test](https://github.com/gpodder/mygpo/commit/603b2ef66aab55ada2b820db571e33ad51acb23b),
Test can be found in **mygpo/userfeeds/tests.py** file.

The function was not being tested at all and had 0% coverage.

![View_or_basicauth Coverage Results](coverage/report_images/hussein_v_or_ba_cov_results.png "View_or_basicauth Coverage Results")

After creating a new test for it, the coverage achieved was **100%**. All different logical paths through the function were taken, and the results were asserted.

#### Mohamed Hussain Shareef

##### Test for Function 1: episode_status_icon in mygpo/web/templatetags/episodes.py

[Link to commit summary with tests](https://github.com/HusseinSarrar05/mygpo/pull/4/files#diff-9b165d03e2d7ee3b32727f3c6a51236d18e30bb4a53aef2b9dd12ecb0ec6578e)

This can be found in **mygpo/web/tests.py**. 
The function previously had no testing, and had 0% coverage. 
After creating new tests for it, 100% coverage was achieved. All branches were taken, and we did different testing scenarios to check for proper statuy icon behaviour. 
See previous section for the coverage results produced after testing. 

##### Test for Function 2: EpisodeUpdater in mygpo/data/feeddownloader.py

This can be found in **mygpo/data/tests.py**

[Link to commit summary with tests](https://github.com/HusseinSarrar05/mygpo/pull/4/files#diff-9866422a779a64f57d1d1143dd58fb30646268710cc5ac465c1b65270b58487c)
The function previously had no testing, and had 0% coverage. 
After creating new tests for it, 100% coverage was achieved. All branches were taken, had to test if it would properly mark episodes as outdated and have proper updating functionality using mock episode objects and assertions. 
See previous section for the coverage results produced after testing. 

### Overall

#### Initial coverage

![Initial Coverage Results](coverage/coverage_before.png "Initial Coverage Results")


<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>


#### Coverage after creating new tests

![Latest Coverage Results](coverage/coverage_after.png "Lates Coverage Results")

#### Result

Achieved an increase of **1.8%** in the **total** coverage of the tests on the project.

## Statement of individual contributions

<Write what each group member did>


### Hussein Sarrar
* Forked github repository and handled creating branches
* Instrumented the **upload** and **view_or_basicauth** functions
* Created new test cases for both functions, achieving 100% coverage on both
* Enured all tests function correctly upon merging

### Mohamed Hussain Sharif
* Counted lines of mygpo using **lizard**
* Instrumented the **episode_status_icon** and **EpisodeUpdater.mark_outdated** functions
* Created new test cases for both functions, achieving 100% coverage on both
* Ran **Coverage.py** on repository before and after merging


### Samuel Power
* Aided in choosing the project and ensuring it was up to requirements
* Instrumented the **episode_status_text** and **normalize_feed_url** functions
* Created new test cases for both functions, achieving 100% coverage on both
*

### Andreas Stolle
* Aided in choosing the project and ensuring it was up to requirements
* Instrumented the **get_urls** and **device_icons** functions
* Created new test cases for both functions, achieving 100% coverage on both
*
