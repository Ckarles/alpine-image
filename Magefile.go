//go:build mage

package main

import (
	"fmt"
	"html/template"
	"io"
	"os"

	"github.com/Masterminds/semver/v3"
	"github.com/magefile/mage/mg"
	"github.com/magefile/mage/sh"
)

type PackerConfig struct {
	Archs         []string
	AlpineVersion string
	SourceMirror  string
}

func (c PackerConfig) SourceBaseURL() string {
	alpineVersion, err := semver.NewVersion(c.AlpineVersion)
	if err != nil {
		panic(err)
	}
	branch := fmt.Sprintf("v%d.%d", alpineVersion.Major(), alpineVersion.Minor())
	return fmt.Sprintf("https://%s/alpine/%s", c.SourceMirror, branch)
}

func (c PackerConfig) SourceVirtISO(arch string) string {
	return fmt.Sprintf("%s/releases/%s/alpine-virt-%s-%s.iso", c.SourceBaseURL(), arch, c.AlpineVersion, arch)
}
func (c PackerConfig) SourceRootfs(arch string) string {
	return fmt.Sprintf("%s/releases/%s/alpine-minirootfs-%s-%s.tar.gz", c.SourceBaseURL(), arch, c.AlpineVersion, arch)
}

func renderPackerTemplate(wr io.Writer, workDir string) error {
	archs := []string{"aarch64", "x86_64"}
	alpineVersion, err := semver.NewVersion("3.18.4")
	if err != nil {
		panic(err)
	}
	alpineMirror := "alpine.global.ssl.fastly.net"

	config := PackerConfig{archs, alpineVersion.String(), alpineMirror}

	tmpl := template.Must(template.ParseGlob("alpine-image_common" + "/templates/*.pkr.hcl.tmpl"))
	tmpl = template.Must(tmpl.ParseGlob(workDir + "/templates/*.pkr.hcl.tmpl"))
	tmpl = template.Must(tmpl.New("packer-template").Parse(`{{ template "main.pkr.hcl.tmpl" . }}`))

	err = tmpl.Execute(wr, config)
	if err != nil {
		return err
	}
	return nil
}

func BuildPackerTemplate(name string) error {
	workDir := "./" + name
	destFileName := workDir + "/" + name + ".pkr.hcl"

	destFile, err := os.Create(destFileName)
	if err != nil {
		return err
	}
	defer destFile.Close()

	return renderPackerTemplate(destFile, workDir)
}

type VagrantfileConfig struct {
	Arch string
}

func BuildVagrantfileTemplates(name string) error {
	archs := []string{"x86_64", "aarch64"}
	for _, arch := range archs {
		workDir := "./" + name
		destFileName := workDir + "/Vagrantfile_" + arch + ".tpl"

		destFile, err := os.Create(destFileName)
		if err != nil {
			return err
		}
		defer destFile.Close()

		config := VagrantfileConfig{arch}
		tmpl := template.Must(template.ParseGlob(workDir + "/templates/Vagrantfile.tpl.tmpl"))
		tmpl = template.Must(tmpl.New("vagrantfile-template").Parse(`{{ template "Vagrantfile.tpl.tmpl" . }}`))

		err = tmpl.Execute(destFile, config)
		if err != nil {
			return err
		}
	}
	return nil
}

func Clean() error {
	for _, d := range []string{"./build", "./dist"} {
		err := os.RemoveAll(d)
		if err != nil {
			return err
		}
	}
	return nil
}

func Build(rootSSHKey string) error {
	mg.Deps(mg.F(BuildPackerTemplate, "alpine-image"))
	mg.Deps(mg.F(BuildPackerTemplate, "alpine-image-vagrant"), mg.F(BuildVagrantfileTemplates, "alpine-image-vagrant"))

	err := sh.RunV("packer", "build", "-var", "root_ssh_key="+rootSSHKey, "alpine-image")
	if err != nil {
		return err
	}
	err = sh.RunV("packer", "build", "-var", "root_ssh_key="+rootSSHKey, "alpine-image-vagrant")
	if err != nil {
		return err
	}
	return nil
}
