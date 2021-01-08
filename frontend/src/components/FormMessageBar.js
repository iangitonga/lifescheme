import React from 'react';


export default class FormMessageBar extends React.Component {
    render() {
        return (
            <div className={`
                form__msg-wrapper
                ${this.props.messageIsShown ? 'form__msg-wrapper--shown ' : ''}
                ${this.props.messageIsSuccess ? 'form__msg-wrapper--success ' : ''}
                ${this.props.messageIsError ? 'form__msg-wrapper--error' : ''}
            `}>
                <div>
                    <span>{this.props.message}</span>
                </div>
            </div>
        );
    }
}
