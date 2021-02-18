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
            choice(name: 'config',
                 defaultValue: '-tfm-build-and-test',
                 choices: ['-tfm-build-and-test', '-tfm-build-only'], 
                 description: 'config choices - basically sub job selection'),
            booleanParam(name: 'run_rebase',
                defaultValue: false,
                description: 'specify whether to run rebase script')
        ])
])

echo "Starting job"
println(env.getEnvironment())
/* TODO: set to wherever the current fork is */
this_fork = "saheerb/mbed-os-tf-m-regression-tests"
this_topic = github.getCurrentBranch()

utils.prettyPrintMap("params in branch job are",params)

/* Do the setup operations */
stage("setup") {
    cipipeline.cinode(label: "ci_general_utility", timeout: 1800) {
            def gitHubBranchId = github.getBranchId(params.mbed_os_topic)
            def s3Bucket = s3.getDefaultBucket()
            def s3BasePath = s3.getBasePath()
            def upstreamBuildNumber = env.BUILD_NUMBER
            def s3SourcePath = "${s3BasePath}/sources/${gitHubBranchId}/${upstreamBuildNumber}/sources.tar.gz"
            dir("mbed-os-tf-m-regression-tests"){
                checkout scm
                sh "git clone https://github.com/${params.mbed_os_fork}.git -b ${params.mbed_os_topic}"
                /* If rebase needed execute that */
                if (params.run_rebase) {
                }
            }
            sh "tar -czf sources.tar.gz mbed-os-tf-m-regression-tests --exclude-vcs"
            // upload source
            s3.upload("sources.tar.gz", s3SourcePath, s3Bucket, "eu-west-1")
    }
}


mbed.run_job([
        subBuildsPostfix         : params.config,
        enableGithubComment      : true,
        targets_toolchains_build : params.targets_toolchains_build,
        targets_toolchains_test  : params.targets_toolchains_test,
        current_fork             : this_fork,
        current_topic            : this_topic,
        mbed_os_fork             : params.mbed_os_fork,
        mbed_os_topic            : params.mbed_os_topic,
        run_rebase               : params.run_rebase,
        isPropagate              : false,
        checkout                 : null
])


