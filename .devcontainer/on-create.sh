#!/bin/bash

function install_packages(){
    # install_packages
    #  - install bash-completion required to use poetry bash-completion
    # - install psql client
    apt-get update -y && apt-get install -y  bash-completion locales &&   apt-get autoremove -y && apt-get autoclean
    locale-gen en_US.UTF-8
    update-locale

    echo 'source /etc/profile' >> ${HOME}/.bashrc

}

function install_poetry(){
    # install_poerty()
    # - installs latest version of poetry
    # - installs command completion for poetry
    pip install poetry
    poetry completions bash > /etc/bash_completion.d/poetry
    poetry self add poetry-plugin-up
    poetry self add poetry-plugin-export
    poetry config warnings.export false
    echo 'source $(poetry env info --path)/bin/activate' >> ${HOME}/.bashrc
}

setup_precommit(){
    source ${HOME}/.bashrc
    pre-commit autoupdate
    pre-commit install
}


install_awscli(){

    local ARCH=""
    if [[ $(arch) == "x86_64" ]]
    then
        ARCH='x86_64'
    elif [[ $(arch) == 'aarch64' || $(arch) == "arm64" ]]
    then
        ARCH="aarch64"
    fi

    local AWSCLI_FILE="/tmp/awscliv2.zip"
    local UNZIP_DIR="/tmp"
    local URL="https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip"

    curl ${URL} -o ${AWSCLI_FILE}
    unzip ${AWSCLI_FILE} -d $UNZIP_DIR
    ${UNZIP_DIR}/aws/install
    rm -rf ${UNZIP_DIR}/aws/
    rm ${AWSCLI_FILE}
}

install_git_bashprompt(){
    git clone https://github.com/magicmonty/bash-git-prompt.git $HOME/.bash-git-prompt --depth=1

    echo -e "if [ -f "$HOME/.bash-git-prompt/gitprompt.sh" ]
then
    GIT_PROMPT_ONLY_IN_REPO=1
    source $HOME/.bash-git-prompt/gitprompt.sh
fi\n" >> $HOME/.bashrc

}


function configure_git(){
    # this configure_git
    # - sets vscode as default editor for git
    # - sets git username if set in the .env file
    #  - sets git email if set in the .env file
    git config --global core.editor "code -w"

    if [ !  -z "${GIT_USER_NAME}" ]
    then
        git config --global user.name "${GIT_USER_NAME}"
    fi

    if [ !  -z "${GIT_EMAIL}" ]
    then
        git config --global user.email "${GIT_EMAIL}"
    fi
}

function install_git_bash_prompt(){
    # install_git_bash_prompt
    #  - install git bash prompt
    #  - configure git bash propmpt
    #  - enable git bash prompt
    if [ ! -d "${HOME}/.bash-git-prompt" ]
    then
        git clone https://github.com/magicmonty/bash-git-prompt.git  ${HOME}/.bash-git-prompt --depth=1

        echo 'if [ -f "${HOME}/.bash-git-prompt/gitprompt.sh" ]; then
        GIT_PROMPT_ONLY_IN_REPO=1
        source "$HOME/.bash-git-prompt/gitprompt.sh"
fi' >> ${HOME}/.bashrc

    fi
}

function install_poetry_packages(){
    # install poerty packages
    # - configure poetry to create virtual env with in project so that vscode can find python interpreter
    # - check if project file exist

    poetry config virtualenvs.in-project true


    if [ -f "poetry.lock" ]
    then
        poetry lock
    fi


    if [ -f "pyproject.toml" ]
    then
        poetry up
        poetry install
    fi
}

function main(){
    # main
    #  - execute functions in a given order

    install_packages
    install_git_bash_prompt
    configure_git
    install_poetry
    install_poetry_packages
    setup_precommit
    install_awscli

}

# call to main
main
