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
                defaultValue:  params.targets_toolchains_build ?: "['ARM_MUSCA_S1':['GNUARM'], 'ARM_MUSCA_B1':['GNUARM']]",
                description: 'Map of target and toolchains to build'),
            string(name: 'targets_toolchains_test',
                defaultValue: params.targets_toolchains_test ?: "['ARM_MUSCA_S1':['GNUARM']]",
                description: 'Map of target and toolchains to test. This must be subset of targets_toolchains_build'),
            string(name: 'mbed_os_fork',
                defaultValue: params.mbed_os_fork ?: 'ARMmbed/mbed-os',
                description: 'If fork specify the organization part in https://github.com/{mbed_os_fork}'),
            string(name: 'mbed_os_topic',
                defaultValue: params.mbed_os_topic ?: 'master',
                description: 'specify the branch of mbed-os in test'),
            booleanParam(name: 'run_rebase',
                defaultValue: params.run_rebase ?: false,
                description: 'specify whether to run rebase script')
        ])
])

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

stage("setup") {
    cipipeline.cinode(label: "all-in-one-build-slave", timeout: 5400) {
            def s3SourcePath = "${s3BasePath}/sources/${gitHubBranchId}/${upstreamBuildNumber}/sources.tar.gz"
            dir("mbed-os-tf-m-regression-tests"){
                checkout scm
                sh "ls"
                sh "git clone https://github.com/${params.mbed_os_fork}.git -b ${params.mbed_os_topic}"
            }
            sh "tar -czf sources.tar.gz mbed-os-tf-m-regression-tests --exclude-vcs"
            // upload source
            s3.upload("sources.tar.gz", s3SourcePath, s3Bucket, "eu-west-1")
    }
}

def testTFM() {
    tfm.testIntegration(
        Eval.me(params.targets_toolchains_build),
        Eval.me(params.targets_toolchains_test),
        upstreamBuildNumber,
        params.mbed_os_fork,
        params.mbed_os_topic,
        s3UploadName,
        s3BasePath,
        true, // s3 upload or not 
        s3.getDefaultBucket(),
        "['default_target':'']",
        false, // is this mbed-os sub
        this_fork,
        this_topic,
        params.run_rebase
    )
}

// results_url adds link to testReport on Greentea currentBuild.description
def results_url = "${env.BUILD_URL}testReport/"
def s3_logs_url = "${gitHubBranchId}/${upstreamBuildNumber}/${s3UploadName}"
cipipeline.setBuildDetails(this_fork, this_topic, gitHubBranchId, s3_logs_url, s3Bucket, results_url)
println("Starting build")
this.testTFM()
