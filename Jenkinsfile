/**
 * TFM integration tests
 */

properties([
        buildDiscarder(
                logRotator(artifactDaysToKeepStr: '',
                        artifactNumToKeepStr: '',
                        numToKeepStr: '200')
        ),
        [$class: 'ThrottleJobProperty', categories: ['ci_secure-targets'], limitOneJobWithMatchingParams: false, maxConcurrentPerNode: 0, maxConcurrentTotal: 0, paramsToUseForLimit: '', throttleEnabled: true, throttleOption: 'category'],
        parameters([
            string(name: 'targets_toolchains_build',
                defaultValue:  '["ARM_MUSCA_S1":["GNUARM"], "ARM_MUSCA_B1":["GNUARM"]]',
                description: 'Map of target and toolchains to build'),
            string(name: 'targets_toolchains_test',
                defaultValue: '["ARM_MUSCA_S1":["GNUARM"]]',
                description: 'Map of target and toolchains to test. This must be subset of targets_toolchains_build'),
            string(name: 'mbed_os_fork',
                defaultValue: 'ARMmbed/mbed-os',
                description: 'If fork specify the organization part in https://github.com/{mbed_os_fork}'),
            string(name: 'mbed_os_topic',
                defaultValue: 'master',
                description: 'specify the branch of mbed-os in test'),
            booleanParam(name: 'run_rebase',
                defaultValue: false,
                description: 'specify whether to run rebase script')
        ])
])

echo "Starting job"

echo "Starting job"
println(env.getEnvironment())
this_fork = "saheerb/mbed-os-tf-m-regression-tests"
this_topic = github.getCurrentBranch()
println(this_topic)
pr_head_sha = github.getPrHeadSha()
github_title = env.JOB_NAME
upstreamBuildNumber = env.BUILD_NUMBER
s3UploadName = env.JOB_NAME
jobTitle = env.JOB_NAME
gitHubBranchId = github.getBranchId(params.mbed_os_topic)
s3Bucket = s3.getDefaultBucket()
s3BasePath = s3.getBasePath()
println(pr_head_sha)


utils.prettyPrintMap("params in branch job are",params)
//env.FORK_NAME = params.mbed_os_fork_name  //"ARMmbed/mbed-os"
//env.BRANCH_NAME = params.mbed_os_branch_name // "master"
//def arr = params.mbed_os_ci_topic.tokenize('/')

mbed.run_job([
        subBuildsPostfix         : "-tfm-standalone",
        enableGithubComment      : true,
        targets_toolchains_build : params.targets_toolchains_build,
        targets_toolchains_test  : params.targets_toolchains_test,
        current_fork             : this_fork,
        current_topic            : this_topic,
        mbed_os_fork             : params.mbed_os_fork,
        mbed_os_topic            : params.mbed_os_topic,
        run_rebase               : params.run_rebase
])


