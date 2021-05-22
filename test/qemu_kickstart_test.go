package test

import (
	"fmt"
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

	fmt.Println(RootDir(t))
	vmName := "test"

	outputDir, err := ioutil.TempDir("", "test-output")
	if err != nil {
		t.Fatalf("cannot create output dir: %v", err)
	}

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
		t.Errorf("did not create an output directory: %s", outputDir)
	}

	qcow2File := filepath.Join(outputDir, vmName+".qcow2")
	if _, err := os.Stat(qcow2File); os.IsNotExist(err) {
		t.Errorf("did not create a .qcow2 image: %s", qcow2File)
	}

	boxFile := filepath.Join(outputDir, vmName+"_libvirt.box")
	if _, err := os.Stat(boxFile); os.IsNotExist(err) {
		t.Errorf("did not create a vagrant box: %s", boxFile)
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
