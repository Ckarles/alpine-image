package test

import (
	"io/ioutil"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/gruntwork-io/terratest/modules/logger"
	"github.com/gruntwork-io/terratest/modules/packer"
)

func TestQemu(t *testing.T) {
	t.Parallel()

	vmName := "test.qcow2"

	outputDir, err := ioutil.TempDir("", "test-output")
	if err != nil {
		t.Fatalf("cannot create output dir: %v", err)
	}

	outputFile := filepath.Join(outputDir, vmName)

	os.RemoveAll(outputDir)
	defer os.RemoveAll(outputDir)

	packerOptions := &packer.Options{
		Template: "packer/alpine.pkr.hcl",
		Vars: map[string]string{
			"output_dir": outputDir,
			"vm_name":    vmName,
		},
		Logger:     logger.Discard,
		WorkingDir: RootDir(t),
	}

	_, err = packer.BuildArtifactE(t, packerOptions)

	if err != nil {
		t.Errorf("artifact build failed: %v", err)
	}

	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		t.Error("did not create an output directory")
	}

	if _, err := os.Stat(outputFile); os.IsNotExist(err) {
		t.Error("did not creates a .qcow2 image")
	}
}

func RootDir(tb testing.TB) string {
	tb.Helper()

	_, b, _, ok := runtime.Caller(0)
	if !ok {
		tb.Fatal("cannot get runtime caller")
	}

	d := path.Join(path.Dir(b))

	return filepath.Dir(d)
}
