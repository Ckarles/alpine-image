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

	// kickstart stage
	vmName := "test"
	outputDir := createAndRemoveTempDir(t)

	runPackerTemplate(t, "stage-kickstart/packer/libvirt.pkr.hcl", outputDir, map[string]string{
		"output_dir": outputDir,
		"vm_name":    vmName,
	})

	qcow2File := filepath.Join(outputDir, vmName+"_libvirt.qcow2")

	assertFileExists(t, outputDir)
	assertFileExists(t, qcow2File)

	// vagrant stage
	inputDir := outputDir
	outputDir = createAndRemoveTempDir(t)

	runPackerTemplate(t, "stage-vagrant/packer/libvirt.pkr.hcl", outputDir, map[string]string{
		"input_dir":  inputDir,
		"output_dir": outputDir,
		"vm_name":    vmName,
	})

	qcow2File = filepath.Join(outputDir, vmName+"_libvirt.qcow2")
	boxFile := filepath.Join(outputDir, vmName+"_libvirt.box")

	assertFileNotExists(t, qcow2File)
	assertFileExists(t, boxFile)

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

func createAndRemoveTempDir(tb testing.TB) string {
	outputDir, err := ioutil.TempDir("", "alpine-base-image-test-*")
	if err != nil {
		tb.Fatalf("cannot create output dir: %v", err)
	}

	os.RemoveAll(outputDir)
	return outputDir
}

func runPackerTemplate(tb testing.TB, template string, outputDir string, options map[string]string) {
	packerOptions := &packer.Options{
		Template:   template,
		Vars:       options,
		Logger:     logger.Discard,
		WorkingDir: RootDir(tb),
	}

	_, err := packer.BuildArtifactE(tb, packerOptions)
	tb.Cleanup(func() {
		os.RemoveAll(outputDir)
	})

	if err != nil {
		tb.Errorf("artifact build failed: %v", err)
	}
}

func assertFileExists(tb testing.TB, path string) {
	tb.Helper()

	if _, err := os.Stat(path); os.IsNotExist(err) {
		tb.Errorf("expected file to exist but it doesn't: %s", path)
	}
}

func assertFileNotExists(tb testing.TB, path string) {
	tb.Helper()

	if _, err := os.Stat(path); os.IsExist(err) {
		tb.Errorf("file exists but should not: %s", path)
	}
}
