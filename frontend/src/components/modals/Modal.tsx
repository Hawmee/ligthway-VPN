import { Modal, ModalBody, ModalContent, ModalHeader } from '@heroui/react';
import type { UseDisclosureReturn } from '@heroui/use-disclosure'
import { type JSX, type ReactNode } from 'react'

interface propsType{
    disclosure : UseDisclosureReturn;
    header ?: string;
    children: ReactNode;
}

function ModalComponent({disclosure , header , children} : propsType)  : JSX.Element{
  return (
    <>
        <Modal size='sm' isOpen={disclosure.isOpen} placement='center' onOpenChange={disclosure.onOpenChange}>
            <ModalContent>
                {
                    <>
                    <ModalHeader className="flex flex-col gap-1 text-lg">{header? header : ''}</ModalHeader>
                    <ModalBody className='text-sm'>
                        {children}
                    </ModalBody>
                    </>
                }
            </ModalContent>
        </Modal>  
    </>
  )
}

export default ModalComponent
